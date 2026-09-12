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
        for name, value in [("local_seeds", lambda: copy.deepcopy(self.seeds)), ("build", lambda x: copy.deepcopy(x))]:
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

    def test_bad_manual_input_prevents_deployable_site(self):
        (self.incoming / "BCMMA.json").write_text("[]")
        with self.assertRaises(c.FeedError):
            self.make()
        self.assertFalse((self.root / "one/site").exists())

    def test_provider_failure_prevents_deployable_site(self):
        with patch.object(c, "build", side_effect=c.FeedError("provider failure")):
            with self.assertRaises(c.FeedError):
                self.make()
        self.assertFalse((self.root / "one/site").exists())

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
