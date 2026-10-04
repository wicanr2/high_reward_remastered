#!/usr/bin/env bash
# 以現行 AppImage 煙霧測試畫面、已接受的戰鬥 HD 對照及本機合成音樂，
# 在 Docker 內製作本機推廣影片。輸出只放 dist-all/<版本>/promo/。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${HR_VERSION:?請設定 HR_VERSION=v.<主>.<次>.<修訂>-YYYYMMDD}"
[[ "$VERSION" =~ ^v\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]{8}$ ]]
DELIVERY="$ROOT/dist-all/$VERSION"
test -d "$DELIVERY" && test -f "$DELIVERY/smoke/linux-title.png"
test -f "$DELIVERY/smoke/linux-newgame.png"
test -f "$ROOT/docs/images/compare-battle.png"
test -f "$ROOT/workplace/out/music/wav/MAP2.wav"
docker image inspect psychicwar-video:latest >/dev/null
timeout "${HR_PROMO_TIMEOUT:-25m}" docker run --rm -i --name hr-promo-render \
  --network none --memory 4g --cpus 2 --pids-limit 256 \
  --log-opt max-size=10m --log-opt max-file=3 \
  -u "$(id -u):$(id -g)" -e "HR_VERSION=$VERSION" \
  -v "$DELIVERY:/delivery" \
  -v "$ROOT/docs/images/compare-battle.png:/battle.png:ro" \
  -v "$ROOT/workplace/out/music/wav/MAP2.wav:/music.wav:ro" \
  psychicwar-video:latest bash -s <<'RENDER'
set -euo pipefail
mkdir -p /delivery/promo
OUT="/delivery/promo/HighReward-${HR_VERSION}-promo.mp4"
FONT=/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc
test -f "$FONT"
FILTER="[0:v]scale=1056:660:flags=neighbor,pad=1280:720:112:0:color=0x101825,drawbox=x=0:y=0:w=iw:h=ih:color=black@0.42:t=fill,drawtext=fontfile=$FONT:text='高報酬戰將':fontcolor=0xF7E6B9:fontsize=76:x=(w-text_w)/2:y=225,drawtext=fontfile=$FONT:text='REMASTERED':fontcolor=white:fontsize=34:x=(w-text_w)/2:y=330,drawtext=fontfile=$FONT:text='DOS 原版 × HD 畫面':fontcolor=0xE6C47A:fontsize=31:x=(w-text_w)/2:y=440,fade=t=in:st=0:d=0.5,fade=t=out:st=7.5:d=0.5,format=yuv420p,setpts=PTS-STARTPTS[v0];
[1:v]scale=1056:660:flags=neighbor,pad=1280:720:112:0:color=0x101825,drawbox=x=0:y=660:w=iw:h=60:color=0x101825:t=fill,drawtext=fontfile=$FONT:text='熟悉的冒險，換上 HD 圖層':fontcolor=0xF7E6B9:fontsize=30:x=(w-text_w)/2:y=671,fade=t=in:st=0:d=0.5,fade=t=out:st=9.5:d=0.5,format=yuv420p,setpts=PTS-STARTPTS[v1];
[2:v]crop=1284:800:1284:0,scale=1056:660:flags=neighbor,pad=1280:720:112:0:color=0x101825,drawbox=x=0:y=660:w=iw:h=60:color=0x101825:t=fill,drawtext=fontfile=$FONT:text='戰場與角色的 HD 呈現':fontcolor=0xF7E6B9:fontsize=30:x=(w-text_w)/2:y=671,fade=t=in:st=0:d=0.5,fade=t=out:st=9.5:d=0.5,format=yuv420p,setpts=PTS-STARTPTS[v2];
[3:v]drawbox=x=240:y=200:w=800:h=3:color=0xD9B56D:t=fill,drawtext=fontfile=$FONT:text='高報酬戰將':fontcolor=0xF7E6B9:fontsize=76:x=(w-text_w)/2:y=255,drawtext=fontfile=$FONT:text='Linux AppImage  ·  Windows ZIP  ·  macOS ZIP':fontcolor=white:fontsize=30:x=(w-text_w)/2:y=385,drawtext=fontfile=$FONT:text='本機完整版  ·  私人驗收':fontcolor=0xD9B56D:fontsize=30:x=(w-text_w)/2:y=470,fade=t=in:st=0:d=0.5,fade=t=out:st=7.5:d=0.5,format=yuv420p,setpts=PTS-STARTPTS[v3];
[v0][v1][v2][v3]concat=n=4:v=1:a=0[v]"
ffmpeg -nostdin -y -hide_banner -loglevel error -nostats -threads 2 -filter_complex_threads 2 \
  -loop 1 -framerate 30 -t 8 -i /delivery/smoke/linux-title.png \
  -loop 1 -framerate 30 -t 10 -i /delivery/smoke/linux-newgame.png \
  -loop 1 -framerate 30 -t 10 -i /battle.png \
  -f lavfi -t 8 -i color=c=0x101825:s=1280x720:r=30 \
  -i /music.wav -filter_complex "$FILTER" -map '[v]' -map 4:a:0 \
  -af 'volume=4dB,afade=t=in:st=0:d=1,afade=t=out:st=34:d=2' \
  -t 36 -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart "$OUT" \
  > /delivery/promo/render.log 2>&1
ffprobe -v error -show_entries format=duration,size,format_name:stream=codec_name,width,height,avg_frame_rate,channels -of json "$OUT" > /delivery/promo/ffprobe.json
ffmpeg -nostdin -hide_banner -nostats -i "$OUT" -vf 'blackdetect=d=0.5:pix_th=0.10' -an -f null - > /delivery/promo/blackdetect.txt 2>&1
ffmpeg -nostdin -hide_banner -nostats -i "$OUT" -af 'silencedetect=noise=-50dB:d=0.5,volumedetect' -vn -f null - > /delivery/promo/audio-check.txt 2>&1
ffmpeg -nostdin -y -hide_banner -loglevel error -i "$OUT" -vf 'fps=1/4,scale=480:270,tile=4x2' -frames:v 1 /delivery/promo/contact.png
sha256sum "$OUT" > /delivery/promo/video-sha256.txt
sha256sum /delivery/smoke/linux-title.png /delivery/smoke/linux-newgame.png /battle.png /music.wav > /delivery/promo/source-sha256.txt
cat > /delivery/promo/rights.json <<EOF
{
  "version": "$HR_VERSION",
  "visibility": "local-only",
  "video": "HighReward-$HR_VERSION-promo.mp4",
  "visuals": [
    {"source": "smoke/linux-title.png", "method": "current packaged AppImage capture", "rights": "original game and HD derivative"},
    {"source": "smoke/linux-newgame.png", "method": "current packaged AppImage capture", "rights": "original game and HD derivative"},
    {"source": "docs/images/compare-battle.png right half", "method": "previous accepted HD comparison capture", "rights": "original game and HD derivative"}
  ],
  "audio": {"source": "workplace/out/music/wav/MAP2.wav", "method": "project FM approximation rendered from original MAP2.MID", "rights": "original composition derivative"},
  "distribution": "No public distribution permission for original game art, text, or music has been established."
}
EOF
echo "$OUT"
RENDER
