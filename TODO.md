# TODO
- Remove cursor.commit and cursor.rollback where unnecessary
- Check plural when locali == 1 in homepage and article page
- Add try...catch to all queries, return None on failure
  - Consider then removing generic Exception and throwing a specific exception
- Try adding generic error page for not logged in and such
- Add edit button next to reservation if owner
- Add try except to image_handler; return False and throw InternalError in Flask;
  - EDIT: no, use generic exceptions instead
- Resize columns in new advertisement