# Functions to work with MySQL book catalog
# - Search by ISBN
# - Search by words
# - Add catalog entry
from books import Book


select_query = "SELECT title, authors, image FROM prints WHERE isbn=%s"
insert_query = "INSERT IGNORE INTO prints (isbn, title, authors, image, lexems) VALUES (%s, %s, %s, %s, %s)"
update_query = "UPDATE prints SET title=%s, authors=%s, image=%s, lexems=%s WHERE isbn=%s"


# Function to add book to MySQl
def add_book(cursor, book, trace=False):
    search_words = ' '.join(book.keys)

    # Check if book with such ISBN exist
    cursor.execute(select_query, (book.isbn,))
    results = cursor.fetchall()

    # Insert if missing
    if len(results) == 0:
        cursor.execute(insert_query, (book.isbn, book.title, book.authors, book.image, search_words))
    # Update if some information missing in the record
    elif (results[0][0] == '' and book.title != '') \
        or (results[0][1] == '' and book.authors != '') \
            or (results[0][2] == '' and book.image != ''):
        if book.title == '':
            book.title = results[0][0]
        if book.authors == '':
            book.authors = results[0][1]
        if book.image == '':
            book.image = results[0][2]
        cursor.execute(update_query, (book.title, book.authors, book.image, search_words, book.isbn))


# MySQL query to search for books
search_query = "SELECT isbn, title, authors, image, MATCH (lexems) AGAINST (? IN BOOLEAN MODE) AS score FROM prints" \
               " WHERE MATCH (lexems) AGAINST (? IN BOOLEAN MODE) ORDER BY score DESC limit 5"


# Function to find book by words
def find_book(cursor, words, trace=False):
    # Only match by two words or more
    words = set([w for w in words if len(w) > 2])

    if len(words) < 1:
        return None, []

    str_words = ' '.join(words)
    if trace:
        print('Call MqSQL with:', str_words)
    cursor.execute(search_query, (str_words, str_words,))

    results = cursor.fetchall()
    if trace:
        print(results)

    # Nothing found
    if len(results) == 0:
        return None, []

    # Get top score and top results
    max_score = results[0][4]
    top_results = [r for r in results if r[4] == max_score]

    # List of books with same top score
    top_books = [Book(isbn, title, authors, image) for isbn, title, authors, image, score in top_results]

    # Find the shortest book among the top ones
    res_len = [len(r[1]) + len(r[2]) for r in top_results]
    i = res_len.index(min(res_len))
    book = top_books[i]

    if trace:
        print('%d book(s) found (%.2f)' % (len(top_books), max_score), [b.title for b in top_books])

    return book, top_books
