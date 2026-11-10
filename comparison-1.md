# Comparison with Ricky Wooten

**The databases hold different book data.** Mine: **9,404 books**. Ricky Wooten: **9,407 books**.

Matched: 9,404. Only mine: 0. Only partner: 3. Differing values in matched books: 0. Ambiguous matches: 0.

## Method

Compared November 9, 2026, using read-only downloaded database snapshots. Map all 23 same-named source columns directly. Exclude internal id values, SQLite sequence values, and runs/run_history tables, as approved. No partner code or tests were read.

Match ISBN-13 first, converting an ISBN-10-only identity to its equivalent ISBN-13. For unmatched rows, match title and authors ignoring case and repeated whitespace only when at least one side has no ISBN. Require a unique fallback match on both sides. Never merge different usable ISBNs by title. No ambiguous matches occurred. Supplier book_id is shown for locating records, not used as identity.

Compare all stored values exactly after matching, including case, whitespace, NULL versus empty text. Normalization is only for matching identities. Columns: `book_id`, `goodreads_book_id`, `best_book_id`, `work_id`, `books_count`, `isbn`, `isbn13`, `authors`, `original_publication_year`, `original_title`, `title`, `language_code`, `average_rating`, `ratings_count`, `work_ratings_count`, `work_text_reviews_count`, `ratings_1`, `ratings_2`, `ratings_3`, `ratings_4`, `ratings_5`, `image_url`, `small_image_url`.

## Only in mine

None.

## Only in Ricky's database

| CSV record | book_id | Title | Stored isbn | Stored isbn13 | Source isbn13 |
|---:|---|---|---|---|---|
| 2895 | 2894 | Sailor Moon, #1 (Sailor Moon, #1) | 189221301X | NULL | 6.45573003012e+11 |
| 3690 | 3689 | The Practice of the Presence of God | 0883681056 | NULL | 6.30809681058e+11 |
| 5269 | 5268 | Anatomy for the Artist | 078948045X | NULL | 6.35517080452e+11 |

Full compared values of each extra book (internal IDs omitted):

### Sailor Moon, #1 (Sailor Moon, #1)

```json
{
  "book_id": "2894",
  "goodreads_book_id": "500503",
  "best_book_id": "500503",
  "work_id": "488611",
  "books_count": "10",
  "isbn": "189221301X",
  "isbn13": null,
  "authors": "Naoko Takeuchi",
  "original_publication_year": "1992.0",
  "original_title": "美少女戦士セーラームーン 1 [Bishōjo Senshi Sailor Moon 1]",
  "title": "Sailor Moon, #1 (Sailor Moon, #1)",
  "language_code": "eng",
  "average_rating": "4.29",
  "ratings_count": "34951",
  "work_ratings_count": "35192",
  "work_text_reviews_count": "391",
  "ratings_1": "996",
  "ratings_2": "1385",
  "ratings_3": "4754",
  "ratings_4": "7181",
  "ratings_5": "20876",
  "image_url": "https://images.gr-assets.com/books/1327981776m/500503.jpg",
  "small_image_url": "https://images.gr-assets.com/books/1327981776s/500503.jpg"
}
```

### The Practice of the Presence of God

```json
{
  "book_id": "3689",
  "goodreads_book_id": "498641",
  "best_book_id": "498641",
  "work_id": "2133549",
  "books_count": "233",
  "isbn": "0883681056",
  "isbn13": null,
  "authors": "Brother Lawrence",
  "original_publication_year": "1691.0",
  "original_title": "The Practice of the Presence of God",
  "title": "The Practice of the Presence of God",
  "language_code": "",
  "average_rating": "4.32",
  "ratings_count": "23889",
  "work_ratings_count": "26303",
  "work_text_reviews_count": "715",
  "ratings_1": "317",
  "ratings_2": "691",
  "ratings_3": "3562",
  "ratings_4": "7427",
  "ratings_5": "14306",
  "image_url": "https://s.gr-assets.com/assets/nophoto/book/111x148-bcc042a9c91a29c1d680899eff700a03.png",
  "small_image_url": "https://s.gr-assets.com/assets/nophoto/book/50x75-a91bf249278a81aabab721ef782c4a74.png"
}
```

### Anatomy for the Artist

```json
{
  "book_id": "5268",
  "goodreads_book_id": "327242",
  "best_book_id": "327242",
  "work_id": "317880",
  "books_count": "5",
  "isbn": "078948045X",
  "isbn13": null,
  "authors": "Sarah Simblet",
  "original_publication_year": "2001.0",
  "original_title": "Anatomy for the Artist",
  "title": "Anatomy for the Artist",
  "language_code": "en-US",
  "average_rating": "3.97",
  "ratings_count": "17000",
  "work_ratings_count": "17050",
  "work_text_reviews_count": "49",
  "ratings_1": "767",
  "ratings_2": "1255",
  "ratings_3": "3413",
  "ratings_4": "3978",
  "ratings_5": "7637",
  "image_url": "https://images.gr-assets.com/books/1309295064m/327242.jpg",
  "small_image_url": "https://images.gr-assets.com/books/1309295064s/327242.jpg"
}
```

## Books in both with different values

None. All 23 values agree for every matched book.

## Snapshot checks

Both partners' published rules.md, books.csv and books-batch2.csv were downloaded for hash verification and match my local copies byte for byte. The difference is not explained by different rules files or source CSV bytes.

- Mine SHA-256: `74ee213735ce18a71d38e3f5e2a773e47264d2c69038722625a44c895543e7bb`
- Partner SHA-256: `6fd7723bd48f4b82858a2cee70d874f44a3459e11f8310b45ae3097a1377b0cf`
- Shared rules SHA-256: `a412e0b51f98360915204a31a1a38da3f26924e101ee295c16d10bb499a16aad`

## Why our data differs

My database has three fewer books than Ricky's: Sailor Moon #1, The Practice of the Presence of God, and Anatomy for the Artist. Everything else matches, including all 23 values for the 9,404 books we both have.

Their source isbn13 values are 6.45573003012e+11, 6.30809681058e+11, and 6.35517080452e+11. These expand to 645573003012, 630809681058, and 635517080452. They are 12-digit numbers rather than 13-digit 978/979 ISBNs. All three have usable ISBN-10s after the permitted leading-zero repair where needed.

My log says "Scientific ISBN-13 does not confirm ISBN-10" for all three. My code applies scientific-notation confirmation first and rejects the disagreement. Ricky stores the ISBN-10 and leaves isbn13 NULL. That result is consistent with applying the other-product-code rule instead. I did not read Ricky's code or tests, so his internal check order is an inference from the database, not a verified implementation fact.

The rules cover both scientific notation and unrelated numeric codes. Our examples cover scientific notation for 978 ISBNs and the ordinary unrelated code 12345, but not a scientific-notation product code paired with a valid ISBN-10. Our tests therefore did not settle that overlap: all 38 passed while this difference remained. It is a rule-precedence edge case and a gap in example coverage, not a difference in column mapping.

I need to ask the team which rule should take priority. We should agree on the wording and an example together before changing shared rules, tests or code. This explanation is a draft based on the CSV, my log and the database comparison. The team discussion has not happened yet.
