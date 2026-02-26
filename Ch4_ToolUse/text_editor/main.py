def greeting():
    print("Hi there")


def calculate_pi(digits=5):
    """
    円周率を指定された小数点以下の桁数まで計算する関数
    ライプニッツの公式を使用: π = 4 * (1 - 1/3 + 1/5 - 1/7 + 1/9 - ...)
    
    Parameters:
    digits (int): 小数点以下の桁数（デフォルト: 5）
    
    Returns:
    float: 計算された円周率の値を小数点以下指定桁数に丸めた値
    """
    pi = 0.0
    # 精度を高めるために十分な反復回数を設定
    iterations = 1000000
    
    for i in range(iterations):
        # ライプニッツの公式
        pi += ((-1) ** i) / (2 * i + 1)
    
    pi *= 4
    
    # 指定された桁数に丸める
    return round(pi, digits)