# Contributing

Thank you for helping. No setup is needed beyond Python 3.10+; the project has
no dependencies.

```bash
python -m unittest discover -s tests     # must pass
python bench/run.py --errors             # shows every pair the matcher gets wrong
```

## Add names to the lexicon (most useful)

Open `src/ismatch/lexicon.py` and add a line:

```
reading[,second reading] = arabic-spelling [other-spelling ...]
```

- The reading is plain ASCII, the way the name is pronounced:
  `husayn = حسين`, `khadija = خديجة`.
- Use `th dh kh gh sh` for ث ذ خ غ ش. Put a dot where two letters would
  wrongly read as one of those: `fat.hi = فتحي`, `is.haq = إسحاق`.
- Do not write ayn or hamza; just the vowel: `ali = علي`, `said = سعيد`.
- If one Arabic spelling has two common readings, list both:
  `malak,malik = ملك`.
- Two names that are spelled differently in Arabic get **separate lines**,
  even if they sound close. That is how the matcher learns they differ.

Family names, regional names (Maghreb, Gulf, Sudan, Iraq, the Levant ...) and
women's names are all under-represented. Every line helps.

## Report a wrong result

Open an issue with the two names, what you expected, and the output of:

```bash
ismatch compare "name one" "name two"
```

## Change the matcher

- Add the failing pairs to `bench/dataset.py` first, then fix.
- Prefer a general rule over a special case for one name.
- **Never tune against `bench/blind.py`.** If a change is motivated by a pair
  in that file, move the pair to `dataset.py` and note it in the changelog,
  so the blind numbers stay honest.
- Keep the library dependency-free.

## Real-world data

Labelled pairs from a real system (even a few hundred, even anonymised to
given names only) would improve this project more than anything else. If you
cannot share data, sharing the precision / recall you measured is still
valuable.
