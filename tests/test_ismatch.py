import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "bench"))

import ismatch  # noqa: E402
from ismatch.cli import main as cli  # noqa: E402
from ismatch.parse import parse_name  # noqa: E402


class SameName(unittest.TestCase):
    def assertSame(self, a, b):
        m = ismatch.compare(a, b)
        self.assertTrue(m.is_match, f"{a!r} vs {b!r} scored {m.score:.2f}\n{m.explain()}")

    def test_arabic_to_latin(self):
        for latin in ("Mohammed", "Muhammad", "Mohamed", "Mohamad", "Mouhamed", "Mo7amed"):
            self.assertSame("محمد", latin)
        self.assertSame("يوسف", "Youssef")
        self.assertSame("خديجة", "Khadidja")
        self.assertSame("عثمان", "Osman")
        self.assertSame("جمال", "Gamal")
        self.assertSame("القذافي", "Gaddafi")

    def test_latin_to_latin(self):
        self.assertSame("Hussein", "Husayn")
        self.assertSame("Hussain", "Hocine")
        self.assertSame("Khaled", "Khalid")
        self.assertSame("Tarek", "Tariq")
        self.assertSame("Rania", "Ranya")

    def test_arabic_spelling_variants(self):
        self.assertSame("أحمد", "احمد")
        self.assertSame("فاطمة", "فاطمه")
        self.assertSame("يحيى", "يحيي")
        self.assertSame("مُحَمَّد", "محمد")
        self.assertSame("عبدالله", "عبد الله")
        self.assertSame("نورالدين", "نور الدين")

    def test_digraph_that_is_two_consonants(self):
        self.assertSame("فتحي", "Fathi")
        self.assertSame("إسحاق", "Ishaq")

    def test_abd_compounds(self):
        for latin in ("Abdulrahman", "Abdul Rahman", "Abd al-Rahman", "Abdel Rahman",
                      "Abderrahmane", "Abdurrahman", "Abd El Rahman"):
            self.assertSame("عبد الرحمن", latin)
            self.assertSame("عبدالرحمن", latin)
        self.assertSame("عبد الله", "Abdullah")
        self.assertSame("Abdallah", "Abdulla")

    def test_article_and_particles(self):
        self.assertSame("Mohammed Al-Hassan", "محمد الحسن")
        self.assertSame("Elsayed", "السيد")
        self.assertSame("Anwar as-Sadat", "أنور السادات")
        self.assertSame("خالد بن الوليد", "Khalid ibn al-Walid")
        self.assertSame("Ben Ali", "Benali")
        self.assertSame("أبو القاسم", "Abulqasim")
        self.assertSame("صلاح الدين", "Salahuddin")

    def test_full_names(self):
        self.assertSame("محمد علي حسن", "Mohamed Ali Hassan")
        self.assertSame("محمد علي حسن", "Hassan, Mohamed Ali")
        self.assertSame("Dr. Ahmed El-Sayed", "أحمد السيد")
        self.assertSame("M. Hassan", "Mohamed Hassan")
        self.assertSame("محمد حسن", "Mohamed Ali Hassan")  # middle name omitted

    def test_hebrew_script(self):
        self.assertSame("מוחמד", "محمد")
        self.assertSame("מוחמד", "Mohammed")
        self.assertSame("ח'אלד", "خالد")
        self.assertSame("חאלד", "Khaled")
        self.assertSame("עבד אל-רחמן", "عبدالرحمن")
        self.assertSame("ג'מאל", "Jamal")


class DifferentName(unittest.TestCase):
    def assertDifferent(self, a, b):
        m = ismatch.compare(a, b)
        self.assertFalse(m.is_match, f"{a!r} vs {b!r} scored {m.score:.2f}\n{m.explain()}")

    def test_known_distinct_names(self):
        self.assertDifferent("حسن", "حسين")
        self.assertDifferent("Hassan", "Hussein")
        self.assertDifferent("حسين", "Hassan")
        self.assertDifferent("חסן", "Hussein")
        self.assertDifferent("محمد", "محمود")
        self.assertDifferent("Mohamed", "Mahmoud")
        self.assertDifferent("Omar", "Amr")
        self.assertDifferent("Khalid", "Khalil")
        self.assertDifferent("Nasser", "Nasr")

    def test_feminine_forms(self):
        self.assertDifferent("منير", "منيرة")
        self.assertDifferent("Samir", "Samira")
        self.assertDifferent("Amin", "Amina")

    def test_compounds(self):
        self.assertDifferent("Abdul Rahman", "Abdul Rahim")
        self.assertDifferent("عبد الله", "عبد الإله")
        self.assertDifferent("صلاح الدين", "نور الدين")

    def test_one_different_part_is_a_different_person(self):
        self.assertDifferent("Mohamed Ali", "Mohamed Hassan")
        self.assertDifferent("Ahmed Mohamed Ali", "Ahmed Mahmoud Ali")
        self.assertDifferent("Omar Hussein Haddad", "Omar Hassan Haddad")
        self.assertDifferent("عمر المختار", "عمر المحتار")

    def test_single_part_is_weak_evidence(self):
        self.assertDifferent("Mohammed", "Mohammed Hassan")


class Api(unittest.TestCase):
    def test_score_range_and_symmetry(self):
        pairs = [("محمد علي", "Ali Mohamed"), ("Fatima", "فاطمة الزهراء"), ("x", "محمد"), ("", "محمد")]
        for a, b in pairs:
            s1, s2 = ismatch.score(a, b), ismatch.score(b, a)
            self.assertTrue(0.0 <= s1 <= 1.0)
            self.assertAlmostEqual(s1, s2, places=6)

    def test_identity(self):
        for name in ("محمد عبد الرحمن الخطيب", "Fatima Zahra", "מוחמד", "Abdulrahman"):
            self.assertAlmostEqual(ismatch.score(name, name), 1.0)

    def test_empty_and_garbage(self):
        self.assertEqual(ismatch.score("", ""), 0.0)
        self.assertEqual(ismatch.score("123 !!!", "محمد"), 0.0)
        self.assertFalse(ismatch.is_match("   ", "Ali"))

    def test_match_object(self):
        m = ismatch.compare("محمد علي", "Ali, Mohamed K.")
        d = m.to_dict()
        self.assertEqual(set(d), {"score", "is_match", "level", "pairs", "unmatched_a", "unmatched_b", "reordered"})
        json.dumps(d)
        self.assertIn("score", m.explain())
        self.assertEqual(bool(m), m.is_match)

    def test_threshold(self):
        self.assertTrue(ismatch.is_match("Hassan", "Hussein", threshold=0.5))
        self.assertFalse(ismatch.is_match("Hassan", "Hussein"))

    def test_keys_are_script_independent(self):
        self.assertEqual(ismatch.keys("محمد"), ("MHMD",))
        self.assertEqual(ismatch.keys("Mohammed"), ("MHMD",))
        self.assertEqual(ismatch.keys("מוחמד"), ("MHMD",))
        self.assertTrue(set(ismatch.keys("عبد الرحمن")) & set(ismatch.keys("Abdurrahman")))

    def test_parse(self):
        toks = parse_name("Dr. Abdul Rahman al-Khatib")
        self.assertEqual([t.forms[0] for t in toks], [("abd", "rahman"), ("khatib",)])
        self.assertEqual(len(parse_name("عبدالرحمن")), 1)
        self.assertEqual(parse_name("A. Hassan")[0].kind, "initial")
        self.assertEqual(parse_name("Abdo")[0].forms[0], ("abdo",))  # a name, not a compound


class IndexAndDedupe(unittest.TestCase):
    NAMES = [
        "محمد علي حسن", "Fatima Zahra", "Yusuf Hasan", "عبد الرحمن الخطيب", "Khalid Mansour",
        "Mohamed Ali Hassan", "Abdulrahman Al-Khatib", "Fatma Zahra", "Hussein Ali", "מוחמד עלי חסן",
    ]

    def test_search(self):
        idx = ismatch.NameIndex(self.NAMES)
        self.assertEqual(len(idx), len(self.NAMES))
        hits = [n for n, _ in idx.search("Muhammad Aly Hasan")]
        self.assertEqual(set(hits), {"محمد علي حسن", "Mohamed Ali Hassan", "מוחמד עלי חסן"})
        self.assertEqual(idx.search("Abd al-Rahman El Khatib")[0][0] in self.NAMES, True)
        self.assertEqual(idx.search("Zzzz Qqqq"), [])
        self.assertEqual(idx.search("Muhammad Aly Hasan", exhaustive=True)[0][1], idx.search("Muhammad Aly Hasan")[0][1])

    def test_search_ids(self):
        idx = ismatch.NameIndex()
        idx.add("خالد منصور", id="rec-7")
        self.assertEqual(idx.search_ids("Khaled Mansur")[0][0], "rec-7")

    def test_dedupe(self):
        clusters = [sorted(self.NAMES[i] for i in g) for g in ismatch.dedupe(self.NAMES)]
        self.assertIn(sorted(["محمد علي حسن", "Mohamed Ali Hassan", "מוחמד עלי חסן"]), clusters)
        self.assertIn(sorted(["عبد الرحمن الخطيب", "Abdulrahman Al-Khatib"]), clusters)
        self.assertIn(sorted(["Fatima Zahra", "Fatma Zahra"]), clusters)
        self.assertEqual(len(clusters), 3)


class Cli(unittest.TestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli(list(args))
        return code, out.getvalue()

    def test_compare(self):
        code, out = self.run_cli("compare", "محمد", "Mohammed", "--json")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["is_match"])
        code, _ = self.run_cli("compare", "Hassan", "Hussein")
        self.assertEqual(code, 1)

    def test_key(self):
        self.assertEqual(self.run_cli("key", "محمد")[1].strip(), "MHMD")

    def test_files(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "people.csv")
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write("id,full_name\n1,محمد علي\n2,Mohamed Aly\n3,Sara Khoury\n")
            code, out = self.run_cli("dedupe", path, "-c", "full_name", "--json")
            self.assertEqual(json.loads(out), [["محمد علي", "Mohamed Aly"]])
            code, out = self.run_cli("search", path, "سارة خوري", "-c", "full_name")
            self.assertEqual(code, 0)
            self.assertIn("Sara Khoury", out)


class Benchmark(unittest.TestCase):
    """Regression guard: quality on the development set must not drop."""

    def test_development_set(self):
        import dataset
        from run import build_pairs, prf

        pos, neg = build_pairs(dataset.GROUPS, dataset.DISTINCT)
        p, r, f = prf([ismatch.score(a, b) for a, b in pos], [ismatch.score(a, b) for a, b in neg],
                      ismatch.DEFAULT_THRESHOLD)
        self.assertGreaterEqual(p, 0.99)
        self.assertGreaterEqual(r, 0.98)


if __name__ == "__main__":
    unittest.main()
