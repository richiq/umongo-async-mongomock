from umongo import Document

# Await syntax related tests are stored in a separate file in order to
# catch a SyntaxError when Python doesn't support it
async def test_await_syntax(db):

    class Doc(Document):

        class Meta:
            collection = db.doc

    async def test_cursor(cursor):
        await cursor.count()
        await cursor.to_list(length=10)
        cursor.rewind()
        await cursor.fetch_next
        _ = cursor.next_object()

    doc = Doc()
    await doc.commit()

    cursor = Doc.find()
    await test_cursor(cursor)
    cursor = doc.find()
    await test_cursor(cursor)
    await Doc.find_one()
    await doc.find_one()
    await Doc.ensure_indexes()
    await doc.ensure_indexes()
    await doc.reload()
    await doc.remove()
