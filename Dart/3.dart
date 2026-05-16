// Problem: Simple Library Management System
//
// Specification:
// Create a simple library management system with the following features:
//
// Requirements:
// 1. Create a `Book` class with:
//    - A constructor that takes title (String), author (String), and isbn (String)
//    - Properties: title, author, isbn, isAvailable (bool, default true)
//    - Methods: borrow(), returnBook(), getBookInfo()
//
// 2. Implement the following business rules:
//    - ISBN must be unique (you can assume input is valid)
//    - A book can only be borrowed if available
//    - A book can only be returned if it was borrowed
//    - Book titles and authors: 1-100 characters, not empty
//
// 3. Create a `Library` class that:
//    - Has a list of Book objects
//    - Methods: addBook(book), borrowBook(isbn), returnBook(isbn), searchBooks(query), getAvailableBooks()
//
// 4. Handle errors appropriately:
//    - Book not found should return null or appropriate message
//    - Attempting to borrow unavailable book should throw exception or return false
//    - Attempting to return available book should throw exception or return false
//
// 5. Create a main function that demonstrates:
//    - Adding books to the library
//    - Borrowing and returning books
//    - Searching for books
//    - Displaying available books
//
// Examples:
// - Add books: "1984" by Orwell, "To Kill a Mockingbird" by Lee
// - Borrow "1984"
// - Try to borrow "1984" again (should fail)
// - Return "1984"
// - Search for books by "Orwell"
// - Display all available books
//
// Constraints:
// - Book titles/authors: 1-100 characters, not empty
// - ISBN: 10-13 characters (assume valid format)
// - Maximum 1000 books per library
//
// Implement the classes and main function below:
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
