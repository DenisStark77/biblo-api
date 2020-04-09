import pandas as pd
from bs4 import BeautifulSoup
import random
import requests
from requests.auth import HTTPProxyAuth
from urllib.parse import quote
import re

from books import Book, is_same_book
from catalog import add_book

proxylist = pd.read_csv('gs://biblosphere-210106.appspot.com/proxylist.csv', sep='\t')

# Function to find book in ABEBOOK bookstore
def lookup_abebooks(bookspine, cursor, trace=False):
    if trace:
        print('Lookup Abebooks for [%s]' % bookspine)

    url = 'https://www.abebooks.com/servlet/SearchResults?kn=%s&sortby=17&pt=book' % quote(bookspine)

    if trace:
        print('URL:', url)

    soup = getAndParseURL(url)
    book_soup = soup.find("div", attrs={"id": "book-1"})

    if book_soup is None:
        if trace:
            print('Book not found in Abebooks')
        return None, False

    # <meta content="9780979862250" itemprop="isbn">
    isbn = book_soup.find('meta', attrs={"itemprop": "isbn"})
    if isbn is not None:
        isbn = isbn.get('content')
        if trace:
            print('ISBN:', isbn)
    else:
        if trace:
            print('ISBN missing for book in Abebooks:', bookspine)
        return None, False

    # <meta content="Title" itemprop="name">
    title = book_soup.find('meta', attrs={"itemprop": "name"})
    if title is not None:
        title = title.get('content')
    else:
        title = ''

    if trace:
        print('Title:', title)

    # <meta content="Author" itemprop="author"/>
    author = book_soup.find('meta', attrs={"itemprop": "author"})
    if author is not None:
        author = author.get('content')
    else:
        author = ''

    if trace:
        print('Author:', author)

    # <img class="srp-item-image"> src
    cover = book_soup.find('img', class_="srp-item-image")
    if cover is not None:
        cover = cover.get('src')
    else:
        cover = ''

    if trace:
        print('Image:', cover)

    if isbn is not None and (title is not None or author is not None):
        book = Book(isbn, title, author, cover)

        # Add book to Biblospere DB anyway
        add_book(cursor, book)

        if is_same_book(title + ' ' + author, bookspine, trace=trace):
            return book, True
        else:
            if trace:
                print('Found book do not match with bookspine:', bookspine, title + ' ' + author)
            return book, False

    return None, False


# Function to find book in LIVELIB website
def lookup_livelib(bookspine, cursor, trace=False):
    if trace:
        print('Lookup Livelib for [%s]' % bookspine)

    url = 'https://www.livelib.ru/find/books/%s' % quote(bookspine)

    if trace:
        print('URL:', url)

    soup = getAndParseURL(url)
    # if trace:
    #    print('SEARCH RESULTS')
    #   print(soup)

    # <div class="object-wrapper object-edition ll-redirect-book" data-link="/book/1000939900-zelenyj-drajver-kod-k-ekologichnoj-zhizni-v-gorode-roman-sablin">
    book_ref_soup = soup.find("div", class_="object-wrapper object-edition ll-redirect-book")
    if book_ref_soup is None:
        if trace:
            print('BOOK LINK MISSED')
            print(soup)
        return None

    link = book_ref_soup.get('data-link')
    if link is None:
        return None

    url = 'https://www.livelib.ru' + link

    if trace:
        print('Book URL:', url)

    soup = getAndParseURL(url)
    # if trace:
    #    print('BOOK PAGE')
    #    print(soup)

    # <div class="block-border card-block">
    book_soup = soup.find("div", class_="block-border card-block")

    if trace:
        print('BOOK PAGE')
        print(book_soup)

    if book_soup is None:
        return None, False

    # <span itemprop="isbn">
    isbn = book_soup.find('span', attrs={"itemprop": "isbn"})
    if isbn is not None:
        isbn = isbn.text.strip()
        if isbn is not None:
            isbn = re.sub('[^0-9]', '', isbn)
        if trace:
            print('ISBN:', isbn)
    else:
        if trace:
            print('ISBN not found on livelib for:', bookspine)
        return None, False

    # <span itemprop="name">Зеленый драйвер. Код к экологичной жизни в городе</span>
    title = book_soup.find('span', attrs={"itemprop": "name"})
    if title is not None:
        title = title.text.strip()
    else:
        title = ''

    if trace:
        print('Title:', title)

    # <a id="book-author" href="/author/503964-roman-sablin" title="Роман Саблин">Роман Саблин</a>
    author = book_soup.find('a', attrs={"id": "book-author"})
    if author is not None:
        author = author.text.strip()
    else:
        author = ''

    if trace:
        print('Author:', author)

    # <img id="main-image-book"
    cover = book_soup.find('img', attrs={"id": "main-image-book"})
    if cover is not None:
        cover = cover.get('src')
    else:
        cover = ''

    if trace:
        print('Image:', cover)

    if isbn is not None and (title is not None or author is not None):
        book = Book(isbn, title, author, cover)

        # Add book to Biblospere DB anyway
        add_book(cursor, book)

        if is_same_book(title + ' ' + author, bookspine, trace=trace):
            return book, True
        else:
            if trace:
                print('Found book do not match with bookspine:', bookspine, title + ' ' + author)
            return book, False

    elif trace:
        print('Book record incomplete on Livelib for:', bookspine)

    return None, False


# Function to find book in OZON bookstore
def lookup_ozon(bookspine, cursor, trace=False):
    if trace:
        print('Lookup Ozon for [%s]' % bookspine)

    url = 'https://www.ozon.ru/category/knigi-16500/?text=%s' % quote(bookspine)

    if trace:
        print('URL:', url)

    soup = getAndParseURL(url)
    # if trace:
    #    print('SEARCH RESULTS')
    #   print(soup)

    # <a data-test-id="tile-name"
    book_ref_soup = soup.find("a", attrs={"data-test-id": "tile-name"})
    if book_ref_soup is None:
        if trace:
            print('BOOK LINK MISSED')
            # print(soup)
        return None, False

    link = book_ref_soup.get('href')
    if link is None:
        return None, False

    url = 'https://www.ozon.ru' + link

    if trace:
        print('Book URL:', url)

    soup = getAndParseURL(url)
    # if trace:
    #    print('BOOK PAGE')
    #    print(soup)

    # <h1 class="b6i0" data-v-41940272><span>
    book_header = soup.find("h1")
    if book_header is not None:
        title = book_header.span.text
        author = ''
        title, author = split_title(title)

    if trace:
        print('Author: %s, Title: %s' % (author, title))

    # <meta data-n-head="true" data-hid="property::og:image" content="https://cdn1.ozone.ru/multimedia/1019366563.jpg" property="og:image">
    cover = soup.find('meta', attrs={"property": "og:image"})
    if cover is not None:
        cover = cover.get('content')
    else:
        cover = ''

    if trace:
        print('Image:', cover)

    isbn = None
    # <div id="section-characteristics"
    book_details = soup.find("div", attrs={"id": "section-characteristics"})
    if book_details is not None:
        # print('Details found: ', book_details)
        spans = book_details.find_all('span')
        for s in spans:
            if s.text == 'Автор':
                dd = s.find_next('dd')
                if dd is not None:
                    a = dd.text
                    if a is not None:
                        # print('Author found: ', a)
                        author = a
            elif s.text == 'Автор на обложке' and author == '':
                dd = s.find_next('dd')
                if dd is not None:
                    a = dd.text
                    if a is not None:
                        # print('Author found: ', a)
                        author = a
            elif s.text == 'ISBN':
                dd = s.find_next('dd')
                if dd is not None:
                    if dd.text is not None:
                        isbn = re.sub('[^0-9\,]', '', dd.text).split(',')[0]
                        # print('ISBN parsed: ', book.isbn)

    if isbn is not None and (title is not None or author is not None):
        book = Book(isbn, title, author, cover)

        # Add book to Biblospere DB anyway
        add_book(cursor, book)

        if is_same_book(title + ' ' + author, bookspine, trace=trace):
            return book, True
        else:
            if trace:
                print('Found book do not match with bookspine:', bookspine, title + ' ' + author)
            return book, False

    elif trace:
        print('Book record incomplete on Ozon for:', bookspine)

    return None, False


# Split title and author separated by |
def split_title(str):
    m = re.compile("(.*)\|(.*)")
    g = m.search(str)
    if g:
        title = g.group(1).rstrip()
        author = g.group(2).lstrip()
    else:
        title = str
        author = ''
    return title, author


# Get a page from the URL via proxy
def getAndParseURL(url):
    i = random.randint(0, 99)
    # print('Proxy used: ', i)
    # proxies = {"http":proxylist['ip'][i]+':'+str(proxylist['port'][i]), "https":proxylist['ip'][i]+':'+str(proxylist['port'][i])}
    proxies = {"http": proxylist['ip'][i] + ':' + str(proxylist['port'][i])}
    auth = HTTPProxyAuth(proxylist['name'][i], proxylist['password'][i])

    result = requests.get(url, proxies=proxies, auth=auth)
    soup = BeautifulSoup(result.content, 'html.parser')
    return (soup)
