# Comparison with John Dries

**The current databases hold the same book data.** Mine: **9,404 books**. John Dries: **9,404 books**.

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

## Books only in John's database

None in the current snapshot.

## Books in both with different values

None. Every compared value agrees.

## Snapshot checks

- My books.db SHA-256: `74ee213735ce18a71d38e3f5e2a773e47264d2c69038722625a44c895543e7bb`
- Partner books.db SHA-256: `8d2d27236a0f23a6698ee15684a3a9a9ecd4a74dd1045a5aae41a73d2a62d264`
- Both published partner rules.md files match my shared rules byte for byte: `a412e0b51f98360915204a31a1a38da3f26924e101ee295c16d10bb499a16aad`.
- Source CSVs were verified byte for byte against both partners on November 9.
- Partner source: https://github.com/jkdries/language-of-computation-week4-assignment/raw/assignment/books.db

## Team discussion

John reported in the November 10 chat that his database matched mine. His posted comparison checked ISBN values; my comparison here checks all 23 approved book columns. Both comparisons found no differences between our books. The same chat discussed Ricky's three extra books and his later correction.

## Why our data differs

My database and John's have the same 9,404 books and the same values in all 23 compared columns. They matched in the first comparison and still match after downloading his current database. There is no book-data difference to explain between us.

We both rejected the three rows that Ricky originally loaded. Our matching results do not by themselves prove that our reading was the only possible one. The team discussion showed that the scientific-notation rule and other-code rule overlapped, and that the examples did not cover this combination. The code I received made that choice without asking me specifically about it. That is the useful finding from comparing all three results.

Ricky later reported adopting the rejection reading. The refreshed comparison with his database is in comparison-1.md. Internal database IDs and run logs were excluded, so this statement is about the catalog data, not identical database files.
