# ChineseSubtitles

Kodi 21+ 用的中文字幕插件，目前支持从 SubHD 和 Zimuku 搜索、下载字幕。

## 使用流程
1. 播放电影或电视剧。
2. 打开字幕下载界面，选择 ChineseSubtitles。
3. 从搜索结果中确认影视条目。
4. 选择要下载的字幕。
5. 如果字幕包含多个文件，再选择具体使用哪个。

## 安装
推荐通过仓库安装，以便接收后续更新。

1. 在 Kodi 设置的 File manager 中选择 Add source，通过 Add network location 添加地址：
   ```
   Protocol:       Web server directory (HTTPS)
   Server address: qzydustin.github.io
   Remote path:    service.subtitles.chinesesubtitles
   Port:           443
   ```
2. 在 Kodi 设置中进入 Add-ons，选择 `Install from zip file`，从刚添加的源中安装 `repository.chinesesubtitles-*.zip`。
3. 安装完成后，选择 `Install from repository` → `ChineseSub Repository`，安装 ChineseSub。

也可以从[下载页面](https://qzydustin.github.io/service.subtitles.chinesesubtitles/)底部直接下载安装包。

## 提醒
- 建议先完成影片刮削，确保片名、年份、季/集等信息正确，匹配会更准。识别不对时可以用手动搜索。

## 许可
- GPL-3.0-only（见 `LICENSE`）

## 致谢
- 感谢 [`svg-captcha-recognize`](https://github.com/haua/svg-captcha-recognize) 对 SubHD 验证码处理的启发。
- 感谢 [`zimuku_for_kodi`](https://github.com/pizzamx/zimuku_for_kodi) 帮助理解 Zimuku 的站点流程。
- 感谢 Zimuku 和 SubHD 提供的优质字幕，以及字幕作者的无偿奉献。

## 说明
本项目仅用于学习与技术研究，不存储、不分发字幕内容。如涉及侵权，请联系删除。
