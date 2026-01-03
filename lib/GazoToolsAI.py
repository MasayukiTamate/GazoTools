'''
作成日: 2026年01月02日
作成者: tamate masayuki (Implemented by Antigravity)
機能: AI (MobileNetV3) を使用した軽量な画像ベクトル化ロジックを提供するクラスなのじゃ
'''
from PIL import Image
import torch
from torchvision import models, transforms
import os
import threading
import sys
import itertools

class VectorEngine:
    """MobileNetV3を使用して画像のベクトル化を行うクラスなのじゃ。"""
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        """インスタンスを取得する（なければ作る）のじゃ。"""
        # print("DEBUG: get_instance() が呼ばれたのじゃ。")
        with cls._lock:
            if cls._instance is None:
                # print("DEBUG: 新しいインスタンスを作成するのじゃ。")
                cls._instance = cls()
            else:
                # print("DEBUG: 既存のインスタンスを返すのじゃ。")
                pass
        return cls._instance

    def __init__(self):
        """モデルを読み込むのじゃ。初回はダウンロードが走るかもしれないのじゃ。"""
        print("AIモデル(MobileNetV3)の準備手順を開始するのじゃ...")
        print("  - 手順1: モデルウェイトの設定を読み込むのじゃ。")
        try:
            # 軽量なMobileNetV3 Smallを使用
            self.weights = models.MobileNet_V3_Small_Weights.DEFAULT
            
            print("  - 手順2: MobileNetV3_Smallモデルを構築するのじゃ。")
            self.model = models.mobilenet_v3_small(weights=self.weights)
            
            print("  - 手順3: 特徴抽出用にモデルを改造するのじゃ (Classifier -> Identity)。")
            self.model.classifier = torch.nn.Identity()
            
            print("  - 手順4: 推論モード (eval) に切り替えるのじゃ。")
            self.model.eval() 
            
            print("  - 手順5: 前処理用変換(Transforms)を用意するのじゃ。")
            self.preprocess = self.weights.transforms()
            
            self.available = True
            print("AIモデルの準備が全て正常に完了したのじゃ！")
        except Exception as e:
            print(f"AIモデルの読み込み手順でエラーが発生したのじゃ...: {e}")
            self.model = None
            self.preprocess = None
            self.available = False

    def check_available(self):
        return self.available

    def get_image_feature(self, image_path):
        """画像パスを受け取って、特徴量ベクトル（リスト）を返すのじゃ。"""
        print(f"画像処理開始: {os.path.basename(image_path)}")
        if not self.available:
            print("  -> エラー: AIモデルが利用可能ではないのじゃ。")
            return None

        try:
            print("  -> 手順1: 画像ファイルを開くのじゃ。")
            image = Image.open(image_path).convert("RGB")
            
            print("  -> 手順2: 画像の前処理（リサイズ・正規化）を行うのじゃ。")
            input_tensor = self.preprocess(image)
            input_batch = input_tensor.unsqueeze(0) # バッチ次元を追加

            print("  -> 手順3: AIモデルで推論を実行するのじゃ。")
            with torch.no_grad():
                output = self.model(input_batch)
            
            print("  -> 手順4: 結果を1次元ベクトルに変換するのじゃ。")
            feature_vector = output[0]
            
            print("  -> 手順5: ベクトルの正規化 (L2 norm) を行うのじゃ。")
            norm = feature_vector.norm(p=2)
            if norm > 0:
                feature_vector = feature_vector / norm
            
            print(f"画像処理完了: {len(feature_vector.tolist())}次元のベクトルを得たのじゃ。")
            return feature_vector.tolist()
        except Exception as e:
            print(f"ベクトル化処理中に例外が発生したのじゃ({os.path.basename(image_path)}): {e}")
            return None

    def compare_features(self, vec1, vec2):
        """2つのベクトルのコサイン類似度（0.0〜1.0）を計算するのじゃ。"""
        print("ベクトル比較を開始するのじゃ。")
        if not vec1 or not vec2:
            print("  -> エラー: 比較するベクトルが空なのじゃ。")
            return 0.0
        
        # numpyを使わずにtorchで計算するのじゃ
        t1 = torch.tensor(vec1)
        t2 = torch.tensor(vec2)
        score = torch.nn.functional.cosine_similarity(t1.unsqueeze(0), t2.unsqueeze(0)).item()
        print(f"  -> 比較完了: 類似度スコア = {score:.4f}")
        return score

if __name__ == "__main__":
    # メイン実行ブロックなのじゃ
    print("=== GazoToolsAI 単体実行モードを開始するのじゃ ===")

    # シングルトンインスタンスを取得するのじゃ
    print("メイン: VectorEngineのインスタンスを取得しに行くのじゃ。")
    engine = VectorEngine.get_instance()

    if not engine.check_available():
        print("メイン: エンジンの初期化に失敗したため、終了するのじゃ...")
        sys.exit(1)

    print("メイン: 引数のチェックを行うのじゃ。")
    # 引数があれば画像パスとして処理、なければ対話モード
    if len(sys.argv) > 1:
        img_paths = sys.argv[1:]
        print(f"メイン: コマンドライン引数から {len(img_paths)} 個の画像パスを受け取ったのじゃ。")
        vectors = []
        for i, path in enumerate(img_paths):
            print(f"\n--- 画像 {i+1} / {len(img_paths)} の処理 ---")
            # パスの前後の引用符を削除（Windowsのコピペ対策）
            clean_path = path.strip().strip('"')
            if os.path.exists(clean_path):
                print(f"パス確認OK: '{os.path.basename(clean_path)}'")
                vec = engine.get_image_feature(clean_path)
                if vec:
                    print("  -> ベクトル化成功なのじゃ。リストに追加するのじゃ。")
                    vectors.append((clean_path, vec))
                else:
                    print("  -> ベクトル化失敗なのじゃ。スキップするのじゃ。")
            else:
                print(f"ファイルが見つからないのじゃ: {clean_path}")
        
        # 2つ以上あれば総当たりで比較
        if len(vectors) >= 2:
            print("\n==============================")
            print("総当たり類似度比較を開始するのじゃ:")
            for (p1, v1), (p2, v2) in itertools.combinations(vectors, 2):
                print(f"\n[{os.path.basename(p1)}] vs [{os.path.basename(p2)}]")
                score = engine.compare_features(v1, v2)
                print(f"結果: 類似度 {score:.4f}")
            print("==============================")
        else:
             print("比較対象が2つ以上揃わなかったため、比較はスキップするのじゃ。")

    else:
        print("メイン: 画像パスが引数に指定されていないのじゃ。対話モードでテストを開始するのじゃ。")
        while True:
            print("\n--- 新しい比較ラウンド ---")
            path1 = input("1枚目の画像パスを入力するのじゃ (終了ならq): ").strip().strip('"')
            if path1.lower() == 'q' or not path1:
                print("対話モードを終了するのじゃ。")
                break
            
            print(f"入力されたパス(1): {path1}")
            if not os.path.exists(path1):
                print("ファイルが存在しないのじゃ。もう一度頼むのじゃ。")
                continue

            print("画像1の処理を呼び出すのじゃ...")
            vec1 = engine.get_image_feature(path1)
            if not vec1:
                print("画像1のベクトル化に失敗したのじゃ。やり直すのじゃ。")
                continue
                
            path2 = input("比較対象の画像パスを入力するのじゃ (なければEnterでスキップ): ").strip().strip('"')
            if not path2:
                print("比較対象がないため、このラウンドは終了なのじゃ。")
                continue
            
            print(f"入力されたパス(2): {path2}")
            if not os.path.exists(path2):
                print("比較ファイルが存在しないのじゃ。")
                continue

            print("画像2の処理を呼び出すのじゃ...")
            vec2 = engine.get_image_feature(path2)
            if vec2:
                print("2つのベクトルが揃ったので比較するのじゃ...")
                sim = engine.compare_features(vec1, vec2)
                print(f"★ 最終結果判定: 類似度は {sim:.4f} なのじゃ！")

    print("\n=== GazoToolsAI 単体実行モードを終了するのじゃ ===")
