"""Offline GitHub/Pages and manual FCI tests; no network or remote publication."""
import base64
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import requests
import github_feed as g
import cloud_feed as c

OLD = [{"date": "2026-09-01", "close": 1.0}]
NEW = OLD + [{"date": "2026-09-02", "close": 2.0}]


class ManualTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.previous = {"BCACCA.json": NEW, "BCAHA.json": OLD, "BCMMA.json": OLD}

    def upload(self, name, rows):
        (self.directory / name).write_bytes(c.encode(rows))

    def test_no_upload_preserves_every_fund(self):
        result, applied, _ = g.apply_fci(self.previous, {}, self.directory)
        self.assertEqual(result, self.previous)
        self.assertEqual(applied, {})

    def test_partial_upload_preserves_older_dates(self):
        self.upload("BCACCA.json", [{"date": "2026-09-03", "close": 3}])
        result, applied, _ = g.apply_fci(self.previous, {}, self.directory)
        self.assertEqual(result["BCACCA.json"], NEW + [{"date": "2026-09-03", "close": 3}])
        self.assertEqual(result["BCAHA.json"], OLD)
        self.assertEqual(set(applied), {"BCACCA.json"})

    def test_new_upload_corrects_only_supplied_dates(self):
        self.upload("BCACCA.json", [{"date": "2026-09-02", "close": 8}])
        result, _, _ = g.apply_fci(self.previous, {}, self.directory)
        self.assertEqual(result["BCACCA.json"], OLD + [{"date": "2026-09-02", "close": 8}])

    def test_repeated_old_upload_does_not_undo_newer_history(self):
        self.upload("BCACCA.json", OLD)
        previous = {**self.previous, "BCACCA.json": [{"date": "2026-09-01", "close": 10}, NEW[-1]]}
        applied = {"BCACCA.json": c.digest(c.encode(OLD))}
        result, _, _ = g.apply_fci(previous, applied, self.directory)
        self.assertEqual(result, previous)

    def test_missing_upload_does_not_remove_applied_marker_or_history(self):
        applied = {"BCACCA.json": c.digest(c.encode(OLD))}
        result, next_applied, _ = g.apply_fci(self.previous, applied, self.directory)
        self.assertEqual(result, self.previous)
        self.assertEqual(next_applied, applied)

    def test_empty_upload_fails_instead_of_clearing_history(self):
        (self.directory / "BCACCA.json").write_text("[]")
        with self.assertRaises(c.FeedError):
            g.apply_fci(self.previous, {}, self.directory)

    def test_txt_or_other_file_rejected(self):
        (self.directory / "BCACCA.txt").write_text('{"historico":[]}')
        with self.assertRaises(c.FeedError):
            g.apply_fci(self.previous, {}, self.directory)


class StagingTests(unittest.TestCase):
    def setUp(self):
        quiet = patch.object(g, "summary")
        quiet.start()
        self.addCleanup(quiet.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.incoming = self.root / "incoming"
        self.incoming.mkdir()
        self.seeds = {n: OLD for n in c.SEEDS}
        for name, value in [("local_seeds", lambda: copy.deepcopy(self.seeds)),
                            ("quicktrade", lambda symbol, old, today: copy.deepcopy(old)),
                            ("dollars", lambda symbol, old, today: copy.deepcopy(old))]:
            mock = patch.object(c, name, value)
            mock.start()
            self.addCleanup(mock.stop)

    def make(self, name="one", client=None, initialize=False):
        path = self.root / name
        g.prepare(path, self.incoming, client, initialize)
        files = {p.name: p.read_bytes() for p in (path / "next-history").iterdir()}
        return path, files

    def test_site_allowlist_and_state_validation(self):
        path, files = self.make()
        self.assertEqual(set(g.read_site(path / "site")), g.SITE_NAMES)
        self.assertNotIn(g.STATE, g.read_site(path / "site"))
        g.validate_history(files)

    def test_corrupt_history_digest_fails(self):
        _, files = self.make()
        files["MEP.json"] = c.encode(NEW)
        with self.assertRaises(c.FeedError):
            g.validate_history(files)

    def test_new_history_wins_over_stale_checkout(self):
        (self.incoming / "BCACCA.json").write_bytes(c.encode(NEW))
        _, files = self.make()
        class Client:
            def load(self):
                return "a" * 40, files
        (self.incoming / "BCACCA.json").unlink()
        path, _ = self.make("two", Client())
        self.assertEqual(c.decode((path / "site/BCACCA.json").read_bytes(), "FCI"), NEW)
        self.assertTrue((path / "previous-site").is_dir())

    def test_missing_history_requires_explicit_initialize(self):
        class Client:
            def load(self):
                return None, None
        with self.assertRaises(c.FeedError):
            self.make(client=Client())
        self.assertFalse((self.root / "one/site").exists())
        self.make(client=Client(), initialize=True)

    def test_bad_manual_input_preserves_fund_and_other_valid_upload(self):
        (self.incoming / "BCMMA.json").write_text("[]")
        (self.incoming / "BCAHA.json").write_bytes(c.encode(NEW))
        path, files = self.make()
        state = g.validate_history(files)
        self.assertEqual(c.decode(files["BCMMA.json"], "FCI"), OLD)
        self.assertEqual(c.decode(files["BCAHA.json"], "FCI"), NEW)
        self.assertNotIn("BCMMA.json", state["applied_fci"])
        self.assertIn("BCMMA.json", json.loads((path / "run.json").read_text())["warnings"])

    def test_all_refreshes_fail_prevents_deployable_site(self):
        with patch.object(c, "quicktrade", side_effect=c.FeedError("provider failure")), \
             patch.object(c, "dollars", side_effect=c.FeedError("provider failure")):
            with self.assertRaisesRegex(c.FeedError, "Ninguna serie"):
                self.make()
        self.assertFalse((self.root / "one/site").exists())

    def test_ccl_failure_does_not_block_mep_bonds_or_fci(self):
        def dollars(symbol, old, today):
            if symbol == "CCL":
                old.clear()  # A failing provider cannot mutate fallback history.
                raise c.FeedError("fecha ausente")
            return NEW
        (self.incoming / "BCAHA.json").write_bytes(c.encode(NEW))
        with patch.object(c, "dollars", side_effect=dollars), patch.object(c, "quicktrade", return_value=NEW):
            path, files = self.make()
        self.assertEqual(c.decode(files["CCL.json"], "CCL"), OLD)
        for name in ["MEP.json", "S30N6.json", "BCAHA.json"]:
            self.assertEqual(c.decode(files[name], name), NEW)
        state = g.validate_history(files)
        report = next(r for r in state['publication']['files'] if r['file'] == 'CCL.json')
        self.assertEqual(report['outcome'], 'retained_after_error')
        self.assertEqual(report['last'], OLD[-1]['date'])
        self.assertEqual(report['error'], 'fecha ausente')
        self.assertEqual(set(g.read_site(path / 'site')), g.SITE_NAMES)

    def test_truncated_series_falls_back_and_unexpected_error_is_sanitized(self):
        self.seeds['AL35.json'] = NEW
        def quote(symbol, old, today):
            if symbol == 'AL35':
                return OLD
            if symbol == 'AE38':
                raise requests.RequestException('private-token')
            return NEW
        with patch.object(c, 'quicktrade', side_effect=quote):
            path, files = self.make()
        self.assertEqual(c.decode(files['AL35.json'], 'AL35'), NEW)
        self.assertEqual(c.decode(files['AE38.json'], 'AE38'), OLD)
        report = (path / 'run.json').read_text()
        self.assertNotIn('private-token', report)
        self.assertIn('RequestException', report)

    def test_invalid_upload_keeps_old_marker_and_retries_when_corrected(self):
        upload = self.incoming / 'BCACCA.json'
        upload.write_bytes(c.encode(NEW))
        _, old_files = self.make()
        class Client:
            def load(self):
                return 'a' * 40, old_files
        upload.write_text('[]')
        _, files = self.make('two', Client())
        state = g.validate_history(files)
        self.assertEqual(state['applied_fci'], g.validate_history(old_files)['applied_fci'])
        self.assertEqual(c.decode(files['BCACCA.json'], 'FCI'), NEW)
        upload.write_bytes(c.encode(NEW + [{'date': '2026-09-03', 'close': 3}]))
        _, repaired = self.make('three', Client())
        self.assertEqual(len(c.decode(repaired['BCACCA.json'], 'FCI')), 3)
        self.assertNotEqual(g.validate_history(repaired)['applied_fci'], state['applied_fci'])

    def test_corrupt_remote_history_still_aborts_everything(self):
        _, files = self.make()
        files['CCL.json'] = b'[]'
        class Client:
            def load(self):
                return 'a' * 40, files
        with self.assertRaises(c.FeedError):
            self.make('two', Client())
        self.assertFalse((self.root / 'two/site').exists())

    def test_mixed_batch_commits_only_after_public_verification(self):
        _, saved = self.make()
        class Client:
            committed = None
            def load(self):
                return 'a' * 40, saved
            def commit(self, files, head):
                self.committed = files
                return 'b' * 40
        client = Client()
        def dollars(symbol, old, today):
            if symbol == 'CCL': raise c.FeedError('missing date')
            return NEW
        with patch.object(c, 'dollars', side_effect=dollars):
            path, files = self.make('two', client)
        with self.assertRaises(c.FeedError): g.commit_history(path, client)
        self.assertIsNone(client.committed)
        run = json.loads((path / 'run.json').read_text())
        site = g.read_site(path / 'site')
        with patch.object(c, 'download_bytes', side_effect=lambda url: (site[url.rsplit('/', 1)[1]], {})):
            g.verify_site(path / 'site', 'https://user.github.io/quotes', attempts=1)
        (path / 'verified.json').write_bytes(g.json_bytes({'generation': run['generation']}))
        g.commit_history(path, client)
        self.assertEqual(client.committed['CCL.json'], saved['CCL.json'])
        self.assertEqual(c.decode(client.committed['MEP.json'], 'MEP'), NEW)
        self.assertEqual(json.loads((path / 'run.json').read_text())['status'], 'published_verified')

    def test_previous_work_is_not_reused(self):
        self.make()
        with self.assertRaises(c.FeedError):
            self.make()

    def test_stable_url_check_rejects_old_manifest(self):
        path, _ = self.make()
        _, second = self.make("two")
        fresh = g.site_from_history(second)
        def fetch(url):
            self.assertNotIn("?", url)
            self.assertNotIn("#", url)
            return fresh[url.rsplit("/", 1)[1]], {}
        with patch.object(c, "download_bytes", side_effect=fetch):
            with self.assertRaises(c.FeedError):
                g.verify_site(path / "site", "https://user.github.io/quotes", attempts=1)

    def test_verifies_each_file_not_just_manifest(self):
        path, _ = self.make()
        site = g.read_site(path / "site")
        site["AL35.json"] = c.encode(NEW)
        with patch.object(c, "download_bytes", side_effect=lambda url: (site[url.rsplit("/", 1)[1]], {})):
            with self.assertRaisesRegex(c.FeedError, "AL35"):
                g.verify_site(path / "site", "https://user.github.io/quotes", attempts=1)

    def test_fixed_urls_pass_when_entire_site_matches(self):
        path, _ = self.make()
        site = g.read_site(path / "site")
        with patch.object(c, "download_bytes", side_effect=lambda url: (site[url.rsplit("/", 1)[1]], {})) as fetch:
            g.verify_site(path / "site", "https://user.github.io/quotes", attempts=1)
        self.assertEqual(fetch.call_count, 19)

    def test_local_or_unverified_build_cannot_commit(self):
        path, _ = self.make()
        with self.assertRaises(c.FeedError):
            g.commit_history(path, None)

    def test_mutated_after_verification_cannot_commit(self):
        class Client:
            def load(self):
                return None, None
        path, _ = self.make(client=Client(), initialize=True)
        run = json.loads((path / "run.json").read_text())
        (path / "verified.json").write_text(json.dumps({"generation": run["generation"]}))
        (path / "site/MEP.json").write_bytes(c.encode(NEW))
        with self.assertRaises(c.FeedError):
            g.commit_history(path, None)


class ApiTests(unittest.TestCase):
    def client(self):
        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "owner/repo", "GITHUB_TOKEN": "private-token"}):
            return g.GitHub()

    def test_transport_does_not_expose_token(self):
        with patch.object(requests, "request", side_effect=requests.RequestException("private-token")) as request:
            with self.assertRaises(c.FeedError) as error:
                self.client().head()
        self.assertNotIn("private-token", str(error.exception))
        self.assertNotIn("private-token", request.call_args.args[1])
        self.assertFalse(request.call_args.kwargs["allow_redirects"])

    def test_current_head_is_pinned_before_writing(self):
        client = self.client()
        with patch.object(g, "validate_history"), patch.object(client, "head", return_value="b" * 40), patch.object(client, "call") as api:
            with self.assertRaises(c.FeedError):
                client.commit({}, "a" * 40)
        api.assert_not_called()

    def test_commit_never_force_pushes_and_preserves_parent(self):
        client = self.client()
        responses = [{"sha": "b" * 40}, {"sha": "c" * 40}, {}]
        with patch.object(g, "validate_history"), patch.object(client, "head", side_effect=["a" * 40, "c" * 40]), patch.object(client, "call", side_effect=responses) as api:
            client.commit({"MEP.json": c.encode(OLD)}, "a" * 40)
        self.assertEqual(api.call_args_list[1].args[2]["parents"], ["a" * 40])
        self.assertEqual(api.call_args_list[2].args[2]["force"], False)

    def test_uncertain_commit_is_verified_not_blindly_retried(self):
        client = self.client()
        responses = [{"sha": "b" * 40}, {"sha": "c" * 40}, c.FeedError("network")]
        with patch.object(g, "validate_history"), patch.object(client, "head", side_effect=["a" * 40, "c" * 40, "c" * 40]), patch.object(client, "call", side_effect=responses) as api:
            self.assertEqual(client.commit({"MEP.json": c.encode(OLD)}, "a" * 40), "c" * 40)
        self.assertEqual(api.call_count, 3)


if __name__ == "__main__":
    unittest.main()
