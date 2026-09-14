# 川崎麻雀倶楽部 iOS ビルド

Unity プロジェクト本体は `C:\Users\Windows\Documents\New project\moonlit-mahjong`。
このリポジトリは Windows で書き出した Xcode プロジェクトを macOS ランナーで署名し、TestFlight へ上げるためのもの。

1. Windows: `Export-iOS.ps1` → `Builds/iOS`（Unity が IL2CPP の C++ と Xcode プロジェクトを生成）
2. Windows: `Publish-iOS.ps1` → `Builds/ios-xcode.zip` を Release `xcode` に上げ、この workflow を起動
3. macOS ランナー: 証明書とプロファイルを用意して `xcodebuild archive` → TestFlight

Secrets（DIST_CERT_BASE64 / DIST_CERT_PASSWORD / KEYCHAIN_PASSWORD / ASC_API_KEY_CONTENT）は FutsunoNews の copy-secrets workflow で複製する。
