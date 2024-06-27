# This is the library project 

### Creating a virtual env
1. py -m virtualenv env
2. .\env\Scripts\activate

### The program

* currently there is only back and no front. the program is tested with "Tunder Client". the program is for managing books in the library.
there are 2 roles: "Admin" and "Customer", each can do specific functions. regular customers can see all books, loan a book, return a book.
Admins can add/update/delete customers/books, get the list of loans and the list of late loans, also they can see all the books. they can't loan/return books. 

### Aplications

1. register- working
2. login- working
3. books- for both admin and customer- working
4. admin/ customers (see all customers)- working
5. admin/ add_user- working
6. admin/ add_book- working
7. admin/ delete_customer/<int:id>- working
8. admin/ update_customer/<int:id>- working
9. admin/ delete_book/<int:id>- working
10. admin/ update_book/<int:id>- working
11. admin/ loans- working
12. admin/ late_loans - doesn't work yet!!!!!
13. customer/ loan_book- working
14. customer/ return_book- working