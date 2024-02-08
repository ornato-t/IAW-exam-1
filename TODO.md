# TODO
- Remove cursor.commit and cursor.rollback where unnecessary
- Add try...catch to all queries, return None on failure
  - Consider then removing generic Exception and throwing a specific exception
- Try adding generic error page for not logged in and such
- Add try except to image_handler; return False and throw InternalError in Flask;
  - EDIT: no, use generic exceptions instead
- Add gradient in home page background