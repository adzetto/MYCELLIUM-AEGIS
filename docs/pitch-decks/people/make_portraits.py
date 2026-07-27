#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ekip fotoğraflarını sunum için tek tip portrelere çevirir.

Kaynak fotoğraflar birbirinden çok farklı: biri siyah-beyaz ve uzaktan,
biri yakın plan selfie, biri iç mekânda boy çekimi. Slaytta yan yana
durduklarında tutarlı görünmeleri için:

  1. Yüz OpenCV ile bulunur, kare kırpım yüzü aynı orana ve aynı dikey
     konuma oturtacak şekilde hesaplanır.
  2. Hepsi aynı tek renk (monokrom + hafif sıcak mürekkep tonu) işlemden
     geçer. Kaynaklardan biri zaten siyah-beyaz olduğu için renkli
     bırakmak uyumsuz duruyordu; tek tip ton bunu kasıtlı bir tasarım
     kararına çeviriyor.
  3. Çıktı 640x640 WebP; slaytta daire olarak maskeleniyor.

Yeniden üretmek için:  python make_portraits.py
"""
import os
import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "portraits")
SIZE = 640

# Yüzün kırpım içindeki hedef oranı ve dikey konumu. Yüz kutusunun
# yüksekliği kırpımın ~%38'i, merkezi de üstten ~%42'sinde olsun; bu,
# vesikalık benzeri dengeli bir çerçeve veriyor.
FACE_FRAC = 0.36
FACE_Y = 0.45

# Deck mürekkebi (#1E2622) yönünde hafif sıcak-nötr ton
TINT = np.array([0.96, 0.985, 0.965])   # R, G, B çarpanları


def find_face(bgr):
    """En büyük yüzü (x, y, w, h) olarak döndür; bulunamazsa None."""
    casc = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    for sf, mn in ((1.05, 6), (1.08, 4), (1.15, 3), (1.25, 2)):
        f = casc.detectMultiScale(gray, scaleFactor=sf, minNeighbors=mn,
                                  minSize=(int(min(gray.shape) * 0.06),) * 2)
        if len(f):
            return max(f, key=lambda r: r[2] * r[3])
    # Gözlük/profil yüzünden bulunamazsa profil sınıflandırıcısını dene
    prof = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_profileface.xml")
    for img in (gray, cv2.flip(gray, 1)):
        f = prof.detectMultiScale(img, 1.08, 4)
        if len(f):
            x, y, w, h = max(f, key=lambda r: r[2] * r[3])
            if img is not gray:                       # aynalanmışı geri çevir
                x = gray.shape[1] - x - w
            return (x, y, w, h)
    return None


def square_crop(im, face):
    """Yüzü hedef orana/konuma oturtan kare kırpım kutusunu hesapla."""
    W, H = im.size
    if face is None:                                   # yedek: orta üst kare
        s = min(W, H)
        return (int((W - s) / 2), int((H - s) * 0.18), s, s)
    fx, fy, fw, fh = face
    cx, cy = fx + fw / 2.0, fy + fh / 2.0
    side = fh / FACE_FRAC
    # Kırpımı önce kenarların izin verdiği en büyük ölçüye indir. Aksi
    # hâlde kutu görüntü dışına taşıyor, sonra içeri çekilirken yüz
    # merkezden kayıyordu (yüz kenara yakın olan karelerde belirgindi).
    side = min(side, W, H,
               2 * cx, 2 * (W - cx),            # yatayda ortalanabilsin
               cy / FACE_Y,                      # üstte yer kalsın
               (H - cy) / (1.0 - FACE_Y))        # altta yer kalsın
    left = cx - side / 2.0
    top = cy - side * FACE_Y
    # kayan nokta artıkları için güvenlik payı
    left = max(0.0, min(left, W - side))
    top = max(0.0, min(top, H - side))
    return (int(round(left)), int(round(top)), int(round(side)), int(round(side)))


def tone(im):
    """Monokrom + hafif ton; kontrastı biraz aç."""
    g = np.asarray(im.convert("L"), dtype=np.float32) / 255.0
    # yumuşak S eğrisi: gölgeleri koru, orta tonu aç
    g = np.clip(1.06 * (g - 0.5) + 0.5 + 0.03, 0.0, 1.0)
    rgb = np.clip(g[..., None] * TINT[None, None, :] * 255.0, 0, 255)
    return Image.fromarray(rgb.astype(np.uint8), "RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    srcs = [f for f in sorted(os.listdir(HERE))
            if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    for fn in srcs:
        path = os.path.join(HERE, fn)
        bgr = cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR)
        if bgr is None:
            print(f"  !! okunamadi: {fn}")
            continue
        im = Image.open(path).convert("RGB")
        face = find_face(bgr)
        x, y, s, _ = square_crop(im, face)
        out = tone(im.crop((x, y, x + s, y + s))
                     .resize((SIZE, SIZE), Image.LANCZOS))
        name = os.path.splitext(fn)[0] + ".webp"
        out.save(os.path.join(OUT, name), "WEBP", quality=88, method=6)
        kb = os.path.getsize(os.path.join(OUT, name)) / 1024
        print(f"  {name:16s} yuz={'var' if face is not None else 'YOK (yedek kirpim)'}"
              f"  kirpim={s}px  ->  {kb:.0f} KB")


if __name__ == "__main__":
    main()
