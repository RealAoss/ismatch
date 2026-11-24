# ismatch

**Match Arabic names across spellings and scripts.**
`محمد` = `Mohammed` = `Muhammad` = `Mohamed` = `מוחמד`, but `حسن` ≠ `حسين`.

Pure Python, zero dependencies, works offline. [العربية](README.ar.md)

[Try the live demo](https://realaoss.github.io/ismatch/demo/) and see which parts of the names match.

```python
>>> import ismatch
>>> ismatch.is_match("محمد عبد الرحمن الخطيب", "Dr. Mohamed Abdelrahman Al-Khatib")
True
>>> ismatch.is_match("Hassan Ali", "Hussein Ali")
False
>>> print(ismatch.compare("Hassan, Mohamed Ali", "محمد علي حسن").explain())
score 1.00  (strong)
  Mohamed  ~  محمد   0.99
  Ali  ~  علي   1.00
  Hassan  ~  حسن   1.00
```

## Why this exists

One Arabic name has dozens of legitimate Latin spellings. There is no single
standard: the spelling depends on the country, the colonial language, the
dialect and the clerk who typed it. *Mohammed* is the most common given name
on earth and is written in well over a dozen ways.

Software that compares names as plain strings gets this wrong in both
directions, and real people pay for it:

- **Hospitals and clinics** create duplicate patient records, splitting one
  person's medical history in two.
- **Humanitarian registration and family tracing** fail to link relatives
  whose names were recorded by different agencies in different scripts.
- **Banks and sanctions screening** freeze accounts of innocent people whose
  name merely resembles a listed one, because generic fuzzy matching cannot
  tell *Hasan* from *Husayn*.
- **Government, university and HR systems** cannot join an Arabic-script
  record to its passport-spelling twin.

Good matchers exist, but they are commercial, or heavy NLP toolkits, or
handle Latin script only. `ismatch` is a small library you can read in an
afternoon and drop into any pipeline.

## What it understands

| Phenomenon | Example |
|---|---|
| Unwritten short vowels | `محمد` ↔ Mohammed / Muhammad / Mohamed |
| Romanisation habits by region | `جمال` ↔ Jamal / Gamal / Djamel · `شريف` ↔ Sharif / Cherif |
| Confusable consonants | `عثمان` ↔ Othman / Osman · `القذافي` ↔ Qaddafi / Gaddafi |
| *Abd* compounds, however spaced | `عبدالرحمن` ↔ Abdul Rahman / Abd al-Rahman / Abderrahmane |
| The article and sun letters | `السيد` ↔ El-Sayed / Elsayed · as-Sadat ↔ `السادات` |
| Particles, titles, initials | `خالد بن الوليد` ↔ Khalid ibn al-Walid · Dr., الحاج, "M. Hassan" |
| Joined / split parts | `صلاح الدين` ↔ Salahuddin · `أبو بكر` ↔ Abubakar · Ben Ali ↔ Benali |
| Arabic spelling variation | `أحمد`/`احمد` · `فاطمة`/`فاطمه` · `يحيى`/`يحيي` · diacritics |
| Name order, omitted middle names | "Hassan, Mohamed Ali" ↔ `محمد علي حسن` |
| Digraphs that are two letters | `فتحي` ↔ Fathi (t + ḥ, not "th") |
| Arabizi | Mo7amed ↔ `محمد` |
| Hebrew script *(experimental)* | `מוחמד` ↔ `محمد` · `ח'אלד` ↔ Khaled |

And, just as important, what it refuses to merge:

| Different names | Why they are hard |
|---|---|
| `حسن` Hasan ≠ `حسين` Husayn | one vowel apart |
| `محمد` Muhammad ≠ `محمود` Mahmud | same consonants |
| `منير` Munir ≠ `منيرة` Munira | masculine / feminine |
| Abdul Rahman ≠ Abdul Rahim | shared first half |
| `عبد الله` ≠ `عبد الإله` | nearly identical letters |
| Ahmed **Mohamed** Ali ≠ Ahmed **Mahmoud** Ali | one different part = another person |

## How it works

1. **Parse** the name: strip diacritics and titles, undo the article, glue
   *Abd* compounds together, drop patronymic particles.
2. **Phonemise** every part into a small script-independent alphabet. Arabic,
   Hebrew and Latin letters all map onto the same consonants and vowel
   classes.
3. **Align** two parts with a weighted edit distance whose costs model how
   names really vary: a Latin vowel facing an unwritten Arabic vowel is nearly
   free; `q`/`k`/`g` or `th`/`t`/`s` are cheap swaps; a missing final vowel is
   expensive because it often marks a feminine name.
4. **Consult a lexicon** of ~450 common names. It supplies the vowels Arabic
   script leaves out and knows that some similar spellings are different
   names.
5. **Assign** the parts of one full name to the parts of the other, tolerate
   reordering and omitted middle names, and punish a clearly different part.

No machine learning, no model download: the result is deterministic and every
score can be explained (`Match.explain()`).

## Accuracy

`python bench/run.py` compares `ismatch` with the approaches people usually
reach for. Each baseline gets the **best possible threshold for that data**;
`ismatch` uses its fixed default (0.85).

| Set | Pairs | Method | Precision | Recall | F1 |
|---|---|---|---|---|---|
| **Blind** (run once, never tuned on) | 2,154 | Levenshtein | 0.662 | 0.552 | 0.602 |
| | | Transliterate + Levenshtein | 0.735 | 0.937 | 0.824 |
| | | Transliterate + consonant skeleton | 0.880 | 0.539 | 0.668 |
| | | **ismatch** | **0.996** | **0.968** | **0.981** |
| Validation (used to find bugs) | 2,055 | Transliterate + Levenshtein | 0.756 | 0.927 | 0.833 |
| | | **ismatch** | 1.000 | 1.000 | 1.000 |
| Development (tuned on) | 2,135 | Transliterate + Levenshtein | 0.807 | 0.929 | 0.864 |
| | | **ismatch** | 1.000 | 0.996 | 0.998 |

Read these numbers with care:

- All three sets were **written by the project authors**, not collected from
  real records. They are full of deliberately confusable pairs, but they are
  not an independent evaluation. Real-world data will be messier.
- Only the **blind** row is an honest estimate. The validation set's first run
  scored precision 0.985 / recall 0.965; the bugs it exposed were then fixed,
  which is why it now reads 1.000.
- If you have labelled name pairs from a real system and can share them (or
  just the aggregate results), please open an issue. That is the most
  valuable contribution this project can receive.

Speed on a laptop, single thread: about 0.1-0.5 ms per comparison; searching
an index of 5,000 names takes about 6 ms; de-duplicating 5,000 names takes
about 9 s (synthetic data built from the lexicon, with 1,000 planted
cross-script duplicates, all found).

## Install

```bash
pip install git+https://github.com/RealAoss/ismatch
```

or clone the repository and run `pip install .`. Python 3.10+.

## Usage

### Compare two names

```python
import ismatch

m = ismatch.compare("عبد الرحمن الخطيب", "Abdurrahman El Khatib")
m.score        # 0.0 - 1.0
m.is_match     # score >= threshold (default 0.85)
m.level        # 'strong' | 'probable' | 'possible' | 'no'
m.pairs        # [(part_a, part_b, similarity), ...]
m.to_dict()    # JSON-ready

ismatch.score(a, b)                    # just the number
ismatch.is_match(a, b, threshold=0.9)  # stricter
```

Choosing a threshold: `0.85` balances both error types. For anything that
blocks a person (sanctions, fraud), keep a human in the loop and treat
`possible` (0.70-0.85) as "needs review", never as a decision.

### Search a list

```python
idx = ismatch.NameIndex(["محمد علي حسن", "Fatima Zahra", "Khalid Mansour"])
idx.add("يوسف الخطيب", id="patient-0042")
idx.search("Muhammad Aly Hasan")        # [('محمد علي حسن', 1.0)]
idx.search_ids("Youssef Al-Khatib")     # [('patient-0042', 0.97)]
```

### Find duplicates

```python
names = ["محمد علي", "Sara Khoury", "Mohamed Aly", "سارة خوري"]
ismatch.dedupe(names)                   # [[0, 2], [1, 3]]  (indexes into names)
```

### Blocking keys for databases

```python
ismatch.keys("محمد")        # ('MHMD',)
ismatch.keys("Mohammed")    # ('MHMD',)
```

Store the keys in an indexed column to fetch candidates with plain SQL, then
score the candidates with `compare`.

### Command line

```bash
ismatch compare "محمد" "Mohammed"             # exit code 0 = match, 1 = no match
ismatch compare "Hassan" "Hussein" --json
ismatch dedupe people.csv --column full_name
ismatch search people.csv "Abd al-Rahman al-Khatib" --column full_name
ismatch key "عبد الرحمن"
```

### In the browser

`demo/index.html` runs the same Python code in the browser through Pyodide;
nothing typed into it leaves the page. Serve the repository root
(`python -m http.server`) and open `/demo/`.

## Limitations

Be aware of these before relying on a score:

- **A name is not an identity.** Two people can share a full name. Combine
  the score with date of birth, place, document number or other evidence.
- **Short and single-part names** carry little information; `Mohammed` alone
  never "matches" `Mohammed Hassan`.
- **Names outside the lexicon** are matched by rules alone. Arabic script
  cannot distinguish two unknown names that differ only in short vowels.
- **Known misses** (from the blind set): `ض` written as *z* (Zia for `ضياء`),
  Turkish *c* for `ج` (Abdulmecid), two different romanisations of `ث`/`ذ`
  compared with each other (Huzaifa / Hothaifa), and Latin pairs that differ
  only in an unstressed vowel (Jabouri / Jabri) can be judged wrongly.
- **Hebrew script support is experimental** and covers Arabic names written
  in Hebrew letters, not Hebrew names in general.
- Persian, Urdu, Turkish and Malay forms of Arabic names are only partly
  covered. Non-Arabic names are compared phonetically with no special
  knowledge.

## Contributing

The easiest high-impact contribution is a line in
[`src/ismatch/lexicon.py`](src/ismatch/lexicon.py): names from your region,
with their vocalised reading. See [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
python -m unittest discover -s tests     # tests
python bench/run.py --errors             # benchmark and every wrong pair
```

## License

MIT
