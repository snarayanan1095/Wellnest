"""
Tests for MongoDB Client
Tests database operations, connection management, and error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.db.mongo import MongoDB


class TestMongoDB:
    """Test suite for MongoDB client"""

    # ===== Connection Tests =====

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful MongoDB connection"""
        with patch('app.db.mongo.AsyncIOMotorClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.admin.command = AsyncMock(return_value={"ok": 1})
            mock_client.return_value = mock_instance

            with patch('app.db.mongo.os.getenv') as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    "MONGODB_URL": "mongodb://localhost:27017",
                    "MONGODB_DATABASE": "test_db"
                }.get(key, default)

                await MongoDB.connect()

                assert MongoDB.client is not None
                assert MongoDB._db_name == "test_db"
                mock_instance.admin.command.assert_called_once_with('ping')

    @pytest.mark.asyncio
    async def test_connect_missing_url(self):
        """Test connection fails when URL is missing"""
        with patch('app.db.mongo.os.getenv', return_value=None):
            with pytest.raises(ValueError, match="MONGODB_URL not found"):
                await MongoDB.connect()

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test connection failure handling"""
        with patch('app.db.mongo.AsyncIOMotorClient') as mock_client:
            mock_instance = MagicMock()
            mock_instance.admin.command = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client.return_value = mock_instance

            with patch('app.db.mongo.os.getenv') as mock_getenv:
                mock_getenv.side_effect = lambda key, default=None: {
                    "MONGODB_URL": "mongodb://localhost:27017",
                    "MONGODB_DATABASE": "test_db"
                }.get(key, default)

                with pytest.raises(Exception, match="Connection failed"):
                    await MongoDB.connect()

    # ===== Write Tests =====

    @pytest.mark.asyncio
    async def test_write_document(self):
        """Test writing a document to MongoDB"""
        mock_collection = MagicMock()
        mock_result = MagicMock()
        mock_result.inserted_id = "test_id_123"
        mock_collection.insert_one = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__ = lambda self, key: mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__ = lambda self, key: mock_db

        MongoDB.client = mock_client
        MongoDB._db_name = "test_db"

        document = {"test": "data", "value": 123}
        result = await MongoDB.write("test_collection", document)

        assert result == "test_id_123"
        mock_collection.insert_one.assert_called_once_with(document)

    @pytest.mark.asyncio
    async def test_write_without_connection(self):
        """Test write fails when not connected"""
        MongoDB.client = None

        with pytest.raises(RuntimeError, match="MongoDB client is not connected"):
            await MongoDB.write("test_collection", {"test": "data"})

    # ===== Read Tests =====

    @pytest.mark.asyncio
    async def test_read_documents(self):
        """Test reading documents from MongoDB"""
        mock_docs = [
            {"_id": "id1", "data": "test1"},
            {"_id": "id2", "data": "test2"}
        ]

        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        mock_cursor.limit = lambda x: mock_cursor
        mock_cursor.sort = lambda x: mock_cursor

        mock_collection = MagicMock()
        mock_collection.find = MagicMock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__ = lambda self, key: mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__ = lambda self, key: mock_db

        MongoDB.client = mock_client
        MongoDB._db_name = "test_db"

        result = await MongoDB.read("test_collection", query={"field": "value"}, limit=2)

        assert len(result) == 2
        # IDs should be converted to strings
        assert all(isinstance(doc["_id"], str) for doc in result)

    @pytest.mark.asyncio
    async def test_read_with_sort(self):
        """Test reading documents with sorting"""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_cursor.limit = lambda x: mock_cursor

        sort_called = False
        def mock_sort(sort_params):
            nonlocal sort_called
            sort_called = True
            return mock_cursor

        mock_cursor.sort = mock_sort

        mock_collection = MagicMock()
        mock_collection.find = MagicMock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__ = lambda self, key: mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__ = lambda self, key: mock_db

        MongoDB.client = mock_client
        MongoDB._db_name = "test_db"

        await MongoDB.read("test_collection", query={}, sort=[("timestamp", 1)])

        assert sort_called

    @pytest.mark.asyncio
    async def test_read_without_limit(self):
        """Test reading all documents without limit"""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[{"_id": "id1"}])

        limit_called = False
        def mock_limit(x):
            nonlocal limit_called
            if x:
                limit_called = True
            return mock_cursor

        mock_cursor.limit = mock_limit
        mock_cursor.sort = lambda x: mock_cursor

        mock_collection = MagicMock()
        mock_collection.find = MagicMock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__ = lambda self, key: mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__ = lambda self, key: mock_db

        MongoDB.client = mock_client
        MongoDB._db_name = "test_db"

        # Call with limit=0 (no limit)
        await MongoDB.read("test_collection", query={}, limit=0)

        # to_list should be called with None when no limit
        mock_cursor.to_list.assert_called_once_with(length=None)

    @pytest.mark.asyncio
    async def test_read_without_connection(self):
        """Test read fails when not connected"""
        MongoDB.client = None

        with pytest.raises(RuntimeError, match="MongoDB client is not connected"):
            await MongoDB.read("test_collection")

    # ===== Distinct Tests =====

    @pytest.mark.asyncio
    async def test_distinct_values(self):
        """Test getting distinct values"""
        mock_collection = MagicMock()
        mock_collection.distinct = AsyncMock(return_value=["value1", "value2", "value3"])

        mock_db = MagicMock()
        mock_db.__getitem__ = lambda self, key: mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__ = lambda self, key: mock_db

        MongoDB.client = mock_client
        MongoDB._db_name = "test_db"

        result = await MongoDB.distinct("test_collection", "field_name")

        assert result == ["value1", "value2", "value3"]
        mock_collection.distinct.assert_called_once_with("field_name", {})

    @pytest.mark.asyncio
    async def test_distinct_with_query(self):
        """Test getting distinct values with query filter"""
        mock_collection = MagicMock()
        mock_collection.distinct = AsyncMock(return_value=["household_001"])

        mock_db = MagicMock()
        mock_db.__getitem__ = lambda self, key: mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__ = lambda self, key: mock_db

        MongoDB.client = mock_client
        MongoDB._db_name = "test_db"

        query = {"date": {"$gte": "2025-01-01"}}
        result = await MongoDB.distinct("events", "household_id", query)

        assert result == ["household_001"]
        mock_collection.distinct.assert_called_once_with("household_id", query)

    # ===== Aggregate Tests =====

    @pytest.mark.asyncio
    async def test_aggregate_pipeline(self):
        """Test running aggregation pipeline"""
        mock_results = [
            {"_id": "household_001", "count": 100},
            {"_id": "household_002", "count": 150}
        ]

        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_results)

        mock_collection = MagicMock()
        mock_collection.aggregate = MagicMock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__ = lambda self, key: mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__ = lambda self, key: mock_db

        MongoDB.client = mock_client
        MongoDB._db_name = "test_db"

        pipeline = [
            {"$match": {"date": "2025-01-15"}},
            {"$group": {"_id": "$household_id", "count": {"$sum": 1}}}
        ]

        result = await MongoDB.aggregate("test_collection", pipeline)

        assert len(result) == 2
        # IDs should be converted to strings
        assert all(isinstance(doc["_id"], str) for doc in result)
        mock_collection.aggregate.assert_called_once_with(pipeline)

    @pytest.mark.asyncio
    async def test_aggregate_without_connection(self):
        """Test aggregate fails when not connected"""
        MongoDB.client = None

        with pytest.raises(RuntimeError, match="MongoDB client is not connected"):
            await MongoDB.aggregate("test_collection", [])

    # ===== Close Tests =====

    @pytest.mark.asyncio
    async def test_close_connection(self):
        """Test closing MongoDB connection"""
        mock_client = MagicMock()
        mock_client.close = MagicMock()

        MongoDB.client = mock_client

        await MongoDB.close()

        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test closing when no client exists"""
        MongoDB.client = None

        # Should not raise exception
        await MongoDB.close()

    # ===== ID Conversion Tests =====

    @pytest.mark.asyncio
    async def test_objectid_to_string_conversion(self):
        """Test that ObjectId is converted to string"""
        from bson import ObjectId

        mock_docs = [
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "data": "test"}
        ]

        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        mock_cursor.limit = lambda x: mock_cursor
        mock_cursor.sort = lambda x: mock_cursor

        mock_collection = MagicMock()
        mock_collection.find = MagicMock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__ = lambda self, key: mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__ = lambda self, key: mock_db

        MongoDB.client = mock_client
        MongoDB._db_name = "test_db"

        result = await MongoDB.read("test_collection")

        # _id should be converted to string
        assert isinstance(result[0]["_id"], str)
        assert result[0]["_id"] == "507f1f77bcf86cd799439011"

    # ===== Query Edge Cases =====

    @pytest.mark.asyncio
    async def test_read_empty_result(self):
        """Test reading when no documents match"""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_cursor.limit = lambda x: mock_cursor
        mock_cursor.sort = lambda x: mock_cursor

        mock_collection = MagicMock()
        mock_collection.find = MagicMock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__ = lambda self, key: mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__ = lambda self, key: mock_db

        MongoDB.client = mock_client
        MongoDB._db_name = "test_db"

        result = await MongoDB.read("test_collection", query={"nonexistent": "value"})

        assert result == []

    @pytest.mark.asyncio
    async def test_read_with_none_query(self):
        """Test reading with None query (should default to empty dict)"""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_cursor.limit = lambda x: mock_cursor
        mock_cursor.sort = lambda x: mock_cursor

        mock_collection = MagicMock()
        find_called_with = None

        def mock_find(query):
            nonlocal find_called_with
            find_called_with = query
            return mock_cursor

        mock_collection.find = mock_find

        mock_db = MagicMock()
        mock_db.__getitem__ = lambda self, key: mock_collection

        mock_client = MagicMock()
        mock_client.__getitem__ = lambda self, key: mock_db

        MongoDB.client = mock_client
        MongoDB._db_name = "test_db"

        await MongoDB.read("test_collection", query=None)

        # Should default to empty dict
        assert find_called_with == {}
