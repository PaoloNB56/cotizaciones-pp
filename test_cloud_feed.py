"""Offline failure/recovery tests. Run: python -B -m unittest -v test_cloud_feed"""
import contextlib
from datetime import date
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import requests
from openpyxl import Workbook
import cloud_feed as c

OLD = [{"date": "2026-09-01", "close": 1.0}]
NEW = OLD + [{"date": "2026-09-02", "close": 2.0}]


class FakeCloud:
    def __init__(self, files, fail=None, uncertain=False):
        self.files = dict(files)
        self.fail = fail
        self.uncertain = uncertain
        self.writes = []

    def read(self, name):
        return self.files.get(name)

    def upload(self, name, body):
        self.writes.append(name)
        if self.uncertain or name != self.fail:
            self.files[name] = body
        if name == self.fail:
            self.fail = None
            raise c.FeedError("network failure")

    def public_check(self, name, body):
        if self.files[name] != body:
            raise c.FeedError("cache mismatch")
        return {}


class ValidationTests(unittest.TestCase):
    def test_bad_series(self):
        bad = [[], {}, {"error": "provider"}, OLD * 2, list(reversed(NEW)),
               [{"date": "2026-02-30", "close": 1}],
               [{"date": "2099-01-01", "close": 1}],
               [{"date": "2026-09-01", "close": v} for v in (None,)]]
        bad += [[{"date": "2026-09-01", "close": v}] for v in (True, "1", 0, -1, float("nan"), float("inf"))]
        bad += [[{"date": "2026-09-01", "close": 1, "secret": "never"}]]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(c.FeedError):
                c.validate(value)

    def test_bom_and_roundtrip(self):
        self.assertEqual(c.decode(b"\xef\xbb\xbf" + c.encode(OLD), "test"), OLD)

    def test_error_page(self):
        with self.assertRaises(c.FeedError):
            c.decode(b"<html>Error 500</html>", "test")

    def test_missing_history(self):
        with self.assertRaises(c.FeedError):
            c.require_coverage(NEW, OLD, "test")

    def test_merge_keeps_old_and_applies_correction(self):
        correction = [{"date": "2026-09-02", "close": 3}]
        self.assertEqual(c.merge(NEW, correction), OLD + correction)

    def test_all_real_seeds(self):
        self.assertEqual(len(c.local_seeds()), 17)

    def test_portable_excel_conversion_and_ticker(self):
        book = Workbook()
        sheet = book.active
        sheet.append(["Símbolo", "Fecha", "Cierre"])
        sheet.append(["S30N6", "02/09/2026", 123.097])
        sheet.append(["S30N6", "01/09/2026", 123.1])
        buffer = io.BytesIO()
        book.save(buffer)
        rows = c.parse_quicktrade(buffer.getvalue(), "S30N6", date(2026, 9, 11))
        self.assertEqual(rows, [{"date": "2026-09-01", "close": 0.1231}, {"date": "2026-09-02", "close": 0.123097}])
        with self.assertRaisesRegex(c.FeedError, "ticker"):
            c.parse_quicktrade(buffer.getvalue(), "AL35", date(2026, 9, 11))

    def test_truncated_excel_history_stops_before_merge(self):
        with patch.object(c.legacy, "descargar_contenido_quicktrade", return_value=b"test"), patch.object(c, "parse_quicktrade", return_value=OLD):
            with self.assertRaisesRegex(c.FeedError, "faltan"):
                c.quicktrade("S30N6", NEW, date(2026, 9, 11))

    def test_dolarazo_malformed_row_is_not_silently_skipped(self):
        payload = {"ok": True, "data": [{"fecha": "2026-09-02", "venta": "error"}]}
        with patch.object(c.legacy, "descargar_json_dolarazo", return_value=payload):
            with self.assertRaises(c.FeedError):
                c.dollars("MEP", OLD, date(2026, 9, 11))

    def test_dolarazo_gap_is_rejected(self):
        history = {"ok": True, "data": [{"fecha": "2026-09-01", "venta": 1}, {"fecha": "2026-09-03", "venta": 3}]}
        current = {"ok": True, "data": {"fechaActualizacion": "2026-09-03T15:00:00Z", "venta": 3}}
        with patch.object(c.legacy, "descargar_json_dolarazo", side_effect=[history, current]):
            with self.assertRaisesRegex(c.FeedError, "hueco"):
                c.dollars("MEP", OLD, date(2026, 9, 11))

    def test_dolarazo_refreshes_same_day(self):
        history = {"ok": True, "data": [{"fecha": "2026-09-01", "venta": 1}]}
        current = {"ok": True, "data": {"fechaActualizacion": "2026-09-01T15:00:00Z", "venta": 2}}
        with patch.object(c.legacy, "descargar_json_dolarazo", side_effect=[history, current]):
            self.assertEqual(c.dollars("MEP", OLD, date(2026, 9, 1)), [{"date": "2026-09-01", "close": 2}])

    def test_local_lock_blocks_second_writer(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(c, "ROOT", Path(tmp)):
            with c.single_local_writer():
                with self.assertRaises(c.FeedError):
                    with c.single_local_writer():
                        pass
            with c.single_local_writer():
                pass


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name)
        self.scope = patch.object(c, "SEEDS", {"AL35.json": "AL35.json", "MEP.json": "MEP.json"})
        self.scope.start()
        self.old = {name: c.encode(OLD) for name in c.SEEDS}
        self.new = {name: NEW for name in c.SEEDS}

    def tearDown(self):
        self.scope.stop()
        self.temp.cleanup()

    def test_success(self):
        client = FakeCloud(self.old)
        self.assertEqual(len(c.publish(client, self.new, self.old, self.work)), 2)
        self.assertEqual(client.files, {name: c.encode(NEW) for name in c.SEEDS})

    def test_uncertain_upload_restores_every_attempt(self):
        client = FakeCloud(self.old, fail="MEP.json", uncertain=True)
        with self.assertRaisesRegex(c.FeedError, "restauraron"):
            c.publish(client, self.new, self.old, self.work)
        self.assertEqual(client.files, self.old)
        self.assertEqual(client.writes, ["AL35.json", "MEP.json", "MEP.json", "AL35.json"])

    def test_bootstrap_never_silently_deletes_new_files(self):
        client = FakeCloud({}, fail="MEP.json", uncertain=True)
        with self.assertRaisesRegex(c.FeedError, "parcial"):
            c.publish(client, self.new, dict.fromkeys(c.SEEDS), self.work)
        report = json.loads((self.work / "recovery.json").read_text())
        self.assertEqual(set(report["new_files_left"]), set(c.SEEDS))

    def test_concurrent_change_stops_before_writes(self):
        client = FakeCloud({**self.old, "MEP.json": c.encode(NEW)})
        with self.assertRaisesRegex(c.FeedError, "cambió"):
            c.publish(client, self.new, self.old, self.work)
        self.assertEqual(client.writes, [])

    def test_same_data_skips_upload(self):
        client = FakeCloud(self.old)
        c.publish(client, {name: OLD for name in c.SEEDS}, self.old, self.work)
        self.assertEqual(client.writes, [])

    def test_missing_remote_requires_bootstrap(self):
        client = FakeCloud({})
        with self.assertRaisesRegex(c.FeedError, "falta el histórico"):
            c.remote_previous(client, {name: OLD for name in c.SEEDS})

    def test_corrupt_remote_never_falls_back_to_seed(self):
        client = FakeCloud({"AL35.json": b"[]"})
        with self.assertRaises(c.FeedError):
            c.remote_previous(client, {name: OLD for name in c.SEEDS}, bootstrap=True)

    def test_remote_not_old_checkout_is_authoritative(self):
        client = FakeCloud({name: c.encode(NEW) for name in c.SEEDS})
        previous, _ = c.remote_previous(client, {name: OLD for name in c.SEEDS})
        self.assertEqual(previous, self.new)


class TransportTests(unittest.TestCase):
    def client(self):
        with patch.dict(c.os.environ, {"PCLOUD_API_HOST": "eapi.pcloud.com", "PCLOUD_FOLDER_ID": "123", "PCLOUD_ACCESS_TOKEN": "private-token", "PCLOUD_PUBLIC_BASE_URL": "https://example.pcloud.link/quotes/"}):
            return c.PCloud()

    def test_no_auth_in_url_or_error(self):
        client = self.client()
        with patch.object(c.requests, "post", side_effect=requests.RequestException("private-token")) as post:
            with self.assertRaises(c.FeedError) as error:
                client.call("listfolder")
        self.assertNotIn("private-token", str(error.exception))
        self.assertNotIn("private-token", post.call_args.args[0])
        self.assertFalse(post.call_args.kwargs["allow_redirects"])
        self.assertEqual(post.call_args.kwargs["data"]["access_token"], "private-token")

    def test_stable_url_cache_cannot_pass_with_nonce(self):
        client = self.client()
        responses = [(c.encode(OLD), {}), (c.encode(NEW), {})]
        with patch.object(c, "download_bytes", side_effect=responses) as fetch:
            with self.assertRaisesRegex(c.FeedError, "coincide=True"):
                client.public_check("AL35.json", c.encode(NEW), attempts=1)
        self.assertEqual(fetch.call_args_list[0].args[0], client.base + "AL35.json")
        self.assertIn("?probe=", fetch.call_args_list[1].args[0])

    def test_unlisted_file_rejected_before_upload(self):
        client = self.client()
        with patch.object(client, "call") as api:
            with self.assertRaises(c.FeedError):
                client.upload("cartera.portfolio", c.encode(OLD))
        api.assert_not_called()

    def test_no_partial_and_no_renaming(self):
        client = self.client()
        body = c.encode(OLD)
        response = {"metadata": [{"name": "AL35.json", "size": len(body), "parentfolderid": 123}]}
        with patch.object(client, "call", return_value=response) as api, patch.object(client, "read", return_value=body):
            client.upload("AL35.json", body)
        self.assertEqual(api.call_args.kwargs["data"], {"folderid": 123, "nopartial": 1})

    def test_api_error_result_is_failure_even_with_http_200(self):
        class Response:
            status_code = 200
            def json(self):
                return {"result": 2008, "error": "private-token"}
        with patch.object(c.requests, "post", return_value=Response()):
            with self.assertRaises(c.FeedError) as error:
                self.client().call("uploadfile")
        self.assertIn("2008", str(error.exception))
        self.assertNotIn("private-token", str(error.exception))

    def test_provider_failure_prevents_all_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeCloud({name: c.encode(rows) for name, rows in c.local_seeds().items()})
            with patch.object(c, "PCloud", return_value=client), patch.object(c, "build", side_effect=c.FeedError("provider failure")):
                with self.assertRaises(c.FeedError):
                    c.execute("update", Path(tmp))
            self.assertEqual(client.writes, [])


if __name__ == "__main__":
    unittest.main()
