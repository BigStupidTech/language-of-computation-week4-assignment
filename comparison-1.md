# Comparison with Ricky Wooten

**The current databases hold the same book data.** Mine: **9,404 books**. Ricky Wooten: **9,404 books**.

Refreshed November 11, 2026, from the partner's published assignment branch. My books.db was opened read-only and was not changed.

| Result | Count |
|---|---:|
| Matched books | 9,404 |
| Only in mine | 0 |
| Only in partner database | 0 |
| Matched books with different values | 0 |
| Different field values | 0 |
| Ambiguous matches | 0 |

## Columns and matching

The schemas were inspected before comparing. They still have the same 23 book-data columns, so the previously approved same-name mapping was reused. Internal id values and runs/run_history tables are excluded. These record implementation details and ingestion history, not the book data being compared.

Compared columns: `book_id`, `goodreads_book_id`, `best_book_id`, `work_id`, `books_count`, `isbn`, `isbn13`, `authors`, `original_publication_year`, `original_title`, `title`, `language_code`, `average_rating`, `ratings_count`, `work_ratings_count`, `work_text_reviews_count`, `ratings_1`, `ratings_2`, `ratings_3`, `ratings_4`, `ratings_5`, `image_url`, `small_image_url`.

Match ISBN-13 first, converting ISBN-10 to the equivalent ISBN-13 where needed. For unmatched rows, use normalized title and author only when at least one side lacks an ISBN. Normalize case and repeated whitespace only for matching. Require a unique match on both sides; do not merge different usable ISBNs by title. Supplier book_id is not used as the identity key.

After matching, compare stored values exactly across all 23 columns, including whitespace and NULL versus empty text. There are no ambiguous matches or differing values. No partner code or tests were read.

## Books only in mine

None.

## Books only in Ricky's database

None in the current snapshot.

## Books in both with different values

None. Every compared value agrees.

## Snapshot checks

- My books.db SHA-256: `74ee213735ce18a71d38e3f5e2a773e47264d2c69038722625a44c895543e7bb`
- Partner books.db SHA-256: `d5a36b6962e7fcafe7c45c7e3dd552db14ee8dfaed1949f547d93b8cbcac8e30`
- Both published partner rules.md files match my shared rules byte for byte: `a412e0b51f98360915204a31a1a38da3f26924e101ee295c16d10bb499a16aad`.
- Source CSVs were verified byte for byte against both partners on November 9.
- Partner source: https://github.com/ricky-wooten/language-of-computation-week4-assignment/raw/assignment/books.db

## Original comparison and team discussion

The November 9 comparison was different. Ricky had 9,407 books and I had 9,404. All shared values matched, but these three books were only in his database:

| book_id | Book | Source isbn | Source isbn13 |
|---|---|---|---|
| 2894 | Sailor Moon, #1 | 189221301X | 6.45573003012e+11 |
| 3689 | The Practice of the Presence of God | 883681056 | 6.30809681058e+11 |
| 5268 | Anatomy for the Artist | 078948045X | 6.35517080452e+11 |

The original Ricky snapshot hash was `6fd7723bd48f4b82858a2cee70d874f44a3459e11f8310b45ae3097a1377b0cf`. The original report and snapshot remain in Git history at commit 46ae69d. This refreshed report does not erase what the first comparison found.

In the November 10 team chat, John described the same three differences. Ricky explained that his version treated these as another kind of code, then said he would use the reading that rejects the rows. His later message said his corrected database matched ours. The November 11 download confirms that result across all 23 columns.

## Why our data differs

Our databases match now, but the first comparison found three extra books in Ricky's. Each had a usable ISBN-10 and an isbn13 written in scientific notation for a 12-digit number. That number was not an ISBN-13.

My code and John's rejected those rows because the scientific-notation value did not agree with the ISBN-13 calculated from ISBN-10. Ricky's earlier database kept the ISBN-10 and left isbn13 blank, following the other-code rule. Both paragraphs could seem relevant, and we had not explicitly settled their order for this case.

The rules left room for the two readings. The examples and my tests did not cover a scientific-notation product code paired with a good ISBN-10. The code I received selected the rejection reading without asking me about that overlap. So the rule wording, the missing test case and the code's interpretation all played a part. Passing all 38 tests did not prove that this edge case was settled.

The team discussion identified the scientific-notation rule as the intended reading for these three rows: if the calculated value does not match, reject. Ricky reported changing his result, and his latest database now matches mine. I kept my own database, rules and tests unchanged. The comparison helped us find an assumption that passing tests alone had not exposed.
