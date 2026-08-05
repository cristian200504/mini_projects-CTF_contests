class Book {
  late String title;
  late String author;
  late String isbn;
  late bool isAvailable;
  Book(this.title, this.author, this.isbn, [this.isAvailable = true]) {
    this.title = title;
    this.author = author;
    this.isbn = isbn;
  }
  bool borrow() {
    if (isAvailable) {
      isAvailable = false;
      return true;
    } else {
      return false;
    }
  }

  bool returnBook() {
    if (!isAvailable) {
      isAvailable = true;
      return true;
    } else {
      return false;
    }
  }

  String getBookInfo() {
    return 'Title: $title, Author: $author, ISBN: $isbn, Available: $isAvailable';
  }
}

class Library {
  List<Book> books = [];
  void addBook(Book book) {
    if (books.length < 1000) {
      books.add(book);
    } else {
      print('Library is full. Cannot add more books.');
    }
  }

  bool borrowBook(String isbn) {
    for (Book book in books) {
      if (book.isbn == isbn) {
        return book.borrow();
      }
    }
    print('Book not found.');
    return false;
  }

  bool returnBook(String isbn) {
    for (Book book in books) {
      if (book.isbn == isbn) {
        return book.returnBook();
      }
    }
    print('Book not found.');
    return false;
  }

  List<Book> searchBooks(String query) {
    List<Book> results = [];
    for (Book book in books) {
      if (book.title.contains(query) || book.author.contains(query)) {
        results.add(book);
      }
    }
    return results;
  }

  List<Book> getAvailableBooks() {
    List<Book> availableBooks = [];
    for (Book book in books) {
      if (book.isAvailable) {
        availableBooks.add(book);
      }
    }
    return availableBooks;
  }
}

int main() {
  Library library = Library();
  library.addBook(Book('1984', 'Orwell', '1234567890'));
  library.addBook(Book('To Kill a Mockingbird', 'Lee', '0987654321'));
  print(library.borrowBook('1234567890')); // true
  print(library.borrowBook('1234567890')); // false
  print(library.returnBook('1234567890')); // true
  print(library.searchBooks('Orwell')[0].getBookInfo()); // Book info
  print(library.getAvailableBooks().length); // 2
  return 0;
}
