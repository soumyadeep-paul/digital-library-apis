# Digital Library API and Schema Definition

## MongoDB Schema

### Users Collection

The `users` collection stores information about the users of the library.

```json
{
  "_id": "ObjectId",
  "username": "String",
  "email": "String (unique)",
  "member_since": "ISODate"
}
```

- **_id**: The unique identifier for the user.
- **username**: The user's chosen name.
- **email**: The user's email address, used for notifications.
- **member_since**: The date the user joined the library.

### Books Collection

The `books` collection stores information about the books in the library's catalog.

```json
{
  "_id": "ObjectId",
  "title": "String",
  "authors": ["String"],
  "isbn": "String (unique)",
  "owner_id": "ObjectId",
  "status": "String",
  "borrower_id": "ObjectId",
  "reservation_pending": "Boolean",
  "return_pending": "Boolean",
  "last_updated": "ISODate"
}
```

- **_id**: The unique identifier for the book.
- **title**: The title of the book.
- **authors**: A list of authors of the book.
- **isbn**: The ISBN of the book. We'll use this to fetch book details.
- **owner_id**: The `_id` of the user who owns the book.
- **status**: The current status of the book. Can be one of: `available`, `reserved`, `borrowed`.
- **borrower_id**: The `_id` of the user who has reserved or borrowed the book. This field is only present when the status is `reserved` or `borrowed`.
- **reservation_pending**: A boolean flag to indicate that a reservation needs confirmation from the owner.
- **return_pending**: A boolean flag to indicate that a return needs confirmation from the owner.
- **last_updated**: The timestamp of the last update to the book's record.

## API Endpoints

### Users

#### `POST /users`

- **Description**: Creates a new user in the system.
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "string"
  }
  ```
- **Responses**:
  - `201 Created`: Returns the newly created user's details.
    ```json
    {
      "id": "string (ObjectId)",
      "username": "string",
      "email": "string",
      "member_since": "string (ISODate)"
    }
    ```
  - `400 Bad Request`: If the request body is invalid or the email already exists.

### Books

#### `POST /books`

- **Description**: Adds a new book to the library catalog using its ISBN. The application will fetch book details (title, author) from an external API using the ISBN.
- **Request Body**:
  ```json
  {
    "isbn": "string",
    "owner_id": "string (ObjectId)"
  }
  ```
- **Responses**:
  - `201 Created`: Returns the newly added book's details.
  - `400 Bad Request`: If the request body is invalid.
  - `404 Not Found`: If the owner is not found or the ISBN is invalid.

#### `GET /books`

- **Description**: Retrieves a list of all available books in the library.
- **Query Parameters**:
  - `search` (optional, string): Filter books by title or author.
- **Responses**:
  - `200 OK`: Returns an array of available books.

#### `POST /books/{book_id}/reserve`

- **Description**: A user requests to reserve a book. This action sets the book's status to `reserved` and `reservation_pending` to `true`.
- **Request Body**:
  ```json
  {
    "borrower_id": "string (ObjectId)"
  }
  ```
- **Responses**:
  - `200 OK`: If the reservation request is successful.
  - `404 Not Found`: If the book or borrower is not found.
  - `409 Conflict`: If the book is not available for reservation.

#### `POST /books/{book_id}/confirm-reservation`

- **Description**: The owner of the book confirms a reservation request. This sets `reservation_pending` to `false` and the status to `borrowed`.
- **Request Body**:
  ```json
  {
    "owner_id": "string (ObjectId)"
  }
  ```
- **Responses**:
  - `200 OK`: If the confirmation is successful.
  - `401 Unauthorized`: If the user is not the owner of the book.
  - `404 Not Found`: If the book is not found.
  - `409 Conflict`: If there is no pending reservation for this book.

#### `POST /books/{book_id}/return`

- **Description**: The borrower initiates the return of a book. This sets `return_pending` to `true`.
- **Request Body**:
  ```json
  {
    "borrower_id": "string (ObjectId)"
  }
  ```
- **Responses**:
  - `200 OK`: If the return request is successful.
  - `401 Unauthorized`: If the user is not the current borrower of the book.
  - `404 Not Found`: If the book is not found.
  - `409 Conflict`: If the book is not currently borrowed.

#### `POST /books/{book_id}/confirm-return`

- **Description**: The owner confirms the return of the book. This sets the book's status back to `available` and removes the `borrower_id`.
- **Request Body**:
  ```json
  {
    "owner_id": "string (ObjectId)"
  }
  ```
- **Responses**:
  - `200 OK`: If the return confirmation is successful.
  - `401 Unauthorized`: If the user is not the owner of the book.
  - `404 Not Found`: If the book is not found.
  - `409 Conflict`: If there is no pending return for this book.
