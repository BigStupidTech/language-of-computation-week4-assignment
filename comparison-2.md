# Comparison with John Dries

**The databases hold the same book data.** Mine: **9,404 books**. John Dries: **9,404 books**.

Matched: 9,404. Only mine: 0. Only partner: 0. Differing values in matched books: 0. Ambiguous matches: 0.

## Method

Compared November 9, 2026, using read-only downloaded database snapshots. Map all 23 same-named source columns directly. Exclude internal id values, SQLite sequence values, and runs/run_history tables, as approved. No partner code or tests were read.

Match ISBN-13 first, converting an ISBN-10-only identity to its equivalent ISBN-13. For unmatched rows, match title and authors ignoring case and repeated whitespace only when at least one side has no ISBN. Require a unique fallback match on both sides. Never merge different usable ISBNs by title. No ambiguous matches occurred. Supplier book_id is shown for locating records, not used as identity.

Compare all stored values exactly after matching, including case, whitespace, NULL versus empty text. Normalization is only for matching identities. Columns: `book_id`, `goodreads_book_id`, `best_book_id`, `work_id`, `books_count`, `isbn`, `isbn13`, `authors`, `original_publication_year`, `original_title`, `title`, `language_code`, `average_rating`, `ratings_count`, `work_ratings_count`, `work_text_reviews_count`, `ratings_1`, `ratings_2`, `ratings_3`, `ratings_4`, `ratings_5`, `image_url`, `small_image_url`.

## Only in mine

None.

## Only in John's database

None.

## Books in both with different values

None. All 23 values agree for every matched book.

## Snapshot checks

Both partners' published rules.md, books.csv and books-batch2.csv were downloaded for hash verification and match my local copies byte for byte. The difference is not explained by different rules files or source CSV bytes.

- Mine SHA-256: `74ee213735ce18a71d38e3f5e2a773e47264d2c69038722625a44c895543e7bb`
- Partner SHA-256: `8d2d27236a0f23a6698ee15684a3a9a9ecd4a74dd1045a5aae41a73d2a62d264`
- Shared rules SHA-256: `a412e0b51f98360915204a31a1a38da3f26924e101ee295c16d10bb499a16aad`

## Why our data differs

My database and John's contain the same 9,404 books and the same values in all 23 compared columns. There are no books on only one side and no differing values in matched books. Internal IDs and run history were excluded, as agreed.

There is no book-data difference to explain here. This does not prove that both programs handle every possible input correctly. It means the final catalog data agrees for these deliveries. Ricky's three extra books are discussed in comparison-1.md. I still need to review this result with John.
