import math
from main import calculate_pi


def test_calculate_pi():
    """
    calculate_pi関数をテストする
    """
    # 円周率を小数点以下5桁まで計算
    result = calculate_pi(5)
    
    # 実際の円周率の値（math.piを使用）
    actual_pi = round(math.pi, 5)
    
    print("=== 円周率計算のテスト ===")
    print(f"計算結果: {result}")
    print(f"実際の値: {actual_pi}")
    print(f"math.pi : {math.pi}")
    
    # 誤差を確認
    error = abs(result - actual_pi)
    print(f"誤差: {error}")
    
    # テスト結果
    if result == actual_pi:
        print("✓ テスト成功: 計算結果が正しいです！")
        return True
    else:
        print(f"✗ テスト失敗: 計算結果が期待値と異なります")
        print(f"  期待値: {actual_pi}")
        print(f"  実際: {result}")
        return False


def test_different_digits():
    """
    異なる桁数でテストする
    """
    print("\n=== 異なる桁数でのテスト ===")
    
    for digits in [1, 2, 3, 4, 5]:
        result = calculate_pi(digits)
        actual = round(math.pi, digits)
        match = "✓" if result == actual else "✗"
        print(f"{match} {digits}桁: 計算結果={result}, 実際={actual}")


if __name__ == "__main__":
    # テストを実行
    test_calculate_pi()
    test_different_digits()
    
    print("\n=== 追加情報 ===")
    print(f"円周率（小数点以下5桁）: {calculate_pi(5)}")
