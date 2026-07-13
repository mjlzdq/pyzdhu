"""
单元测试 - DataReader 数据文件读取器

测试：
- CSV 读取（各种编码和格式）
- XLSX 读取
- 自动格式检测
- 类型自动转换
- 边界情况处理
"""
import pytest

from common.data_reader import DataReader


class TestDataReaderCSV:
    """CSV 读取测试"""

    def test_read_valid_csv(self):
        """读取有效的 CSV 文件"""
        rows = DataReader.read_csv("data/sample_posts.csv")
        assert len(rows) >= 4
        assert rows[0]["case_id"] == "DDT-001"
        assert "title" in rows[0]

    def test_csv_has_row_numbers(self):
        """每行应包含 _row_num"""
        rows = DataReader.read_csv("data/sample_posts.csv")
        assert "_row_num" in rows[0]
        assert rows[0]["_row_num"] >= 2  # 从第2行开始（第1行是表头）

    def test_csv_auto_convert_numbers(self):
        """数字应自动转换"""
        rows = DataReader.read_csv("data/sample_posts.csv")
        assert isinstance(rows[0]["expected_status"], int)
        assert isinstance(rows[0]["expected_userId"], int)

    def test_csv_file_not_found(self):
        """不存在的文件应抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError, match="不存在"):
            DataReader.read_csv("data/nonexistent.csv")


class TestDataReaderXLSX:
    """XLSX 读取测试"""

    def test_read_valid_xlsx(self):
        """读取有效的 XLSX 文件"""
        filepath = "data/sample_posts.xlsx"
        try:
            rows = DataReader.read_xlsx(filepath)
        except FileNotFoundError:
            pytest.skip("XLSX 文件不存在")
        except ImportError:
            pytest.skip("openpyxl 未安装")

        assert len(rows) >= 4
        assert rows[0]["case_id"] == "DDT-001"

    def test_xlsx_row_numbers(self):
        """每行应包含 _row_num"""
        filepath = "data/sample_posts.xlsx"
        try:
            rows = DataReader.read_xlsx(filepath)
        except (FileNotFoundError, ImportError):
            pytest.skip("XLSX 文件不存在或 openpyxl 未安装")

        assert "_row_num" in rows[0]


class TestDataReaderAutoDetect:
    """自动格式检测测试"""

    def test_auto_read_csv(self):
        rows = DataReader.read("data/sample_posts.csv")
        assert len(rows) > 0
        assert rows[0]["case_id"] == "DDT-001"

    def test_auto_read_xlsx(self):
        filepath = "data/sample_posts.xlsx"
        try:
            rows = DataReader.read(filepath)
        except (FileNotFoundError, ImportError):
            pytest.skip("XLSX 文件不存在或 openpyxl 未安装")
        assert len(rows) > 0

    def test_unsupported_format(self):
        with pytest.raises(ValueError, match="不支持的文件格式"):
            DataReader.read("data/sample_posts.json")


class TestDataReaderAutoConvert:
    """_auto_convert 类型转换测试"""

    def test_empty_string(self):
        assert DataReader._auto_convert("") == ""

    def test_none_string(self):
        assert DataReader._auto_convert("none") is None
        assert DataReader._auto_convert("null") is None
        assert DataReader._auto_convert("None") is None

    def test_boolean(self):
        assert DataReader._auto_convert("true") is True
        assert DataReader._auto_convert("false") is False
        assert DataReader._auto_convert("TRUE") is True
        assert DataReader._auto_convert("False") is False

    def test_integer(self):
        assert DataReader._auto_convert("123") == 123
        assert DataReader._auto_convert("0") == 0
        assert DataReader._auto_convert("-456") == -456

    def test_float(self):
        assert DataReader._auto_convert("3.14") == 3.14
        assert DataReader._auto_convert("0.5") == 0.5

    def test_json_object(self):
        result = DataReader._auto_convert('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_array(self):
        result = DataReader._auto_convert('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_invalid_json_fallback_to_string(self):
        result = DataReader._auto_convert('{invalid json')
        assert isinstance(result, str)
        assert result == '{invalid json'

    def test_plain_string(self):
        assert DataReader._auto_convert("hello world") == "hello world"


class TestDataReaderDetectFormat:
    """detect_format 格式检测测试"""

    def test_detect_simple_format(self):
        rows = DataReader.read_csv("data/sample_posts.csv")
        fmt = DataReader.detect_format(rows)
        assert fmt == "simple"

    def test_detect_generic_format(self):
        rows = DataReader.read_csv("data/sample_generic.csv")
        fmt = DataReader.detect_format(rows)
        assert fmt == "generic"

    def test_detect_unknown_format(self):
        rows = [{"unknown_field": "value"}]
        fmt = DataReader.detect_format(rows)
        assert fmt == "unknown"

    def test_detect_empty_rows(self):
        fmt = DataReader.detect_format([])
        assert fmt == "unknown"


class TestDataReaderEdgeCases:
    """边界情况测试"""

    def test_utf8_bom(self):
        """UTF-8 BOM 编码应正确处理"""
        rows = DataReader.read_csv("data/sample_posts.csv", encoding="utf-8-sig")
        assert len(rows) > 0
        # 不应有 BOM 字符在 key 中
        assert rows[0]["case_id"] == "DDT-001"
        assert not rows[0]["case_id"].startswith("\ufeff")
