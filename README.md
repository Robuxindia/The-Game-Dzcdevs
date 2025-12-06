# The Game - Basit Voxel Oyun (Pygame + PyOpenGL)

Bu proje Pygame ve PyOpenGL kullanarak basit bir 3D voxel (Minecraft benzeri) oynanış ve görev sistemi gösterir.

Hedefler:
- Küçük voxel world (ör. 16x8x16) ray/kuvvet olmayan basit küp renderer.
- Bir görev listesi: görevler tamamlandığında bildirim gösterilsin.
- Basit hareket (WASD), fare ile bakış.

Kurulum:
1. Python 3.10+ kurun.
2. Sanal ortam oluşturun: `python -m venv .venv` ve aktif edin.
3. Bağımlıkları yükleyin: `pip install -r requirements.txt`.

Çalıştırma:
- `python main.py`

Notlar:
- Bu bir minimal demo. Daha ileri özellikler (blok yerleştirme, fizik, ağ) eklenebilir.
Texture atlas:
- Eğer `textures/blocks.png` dosyasını proje içine koyarsanız (Minecraft 1.21.9 uyumlu atlas), engine otomatik yüklemeye çalışır ve küpler üzerinde atlasın tamamını gösterir (basit demo).

Performans:
	- FPS hedefi için `world.py` içinde `max_draw_distance` değerini 30'dan daha küçük bir değere (ör. 20) ayarlayabilirsiniz.

Texture atlas kullanımı:
	- Eğer gerçek Minecraft atlas'ını kullanıyorsanız, atlasın boyutunu (ör. 256x256) ve her blok için hücre koordinatlarını (tile x,y) verin; ben `block_texture_map` sözlüğünü doldurup UV hesaplamasını ekleyeyim.

Ursina demo (texture test için):
- Eğer texture binding OpenGL tarafında sorun çıkarıyorsa, hızlıca `ursina_demo.py` ile atlasınızı test edebilirsiniz. Kurulum için `requirements.txt` içinde `ursina` eklendi.
- Çalıştırmak için:
```powershell
pip install -r .\requirements.txt
python .\ursina_demo.py

Ursina ana oyun (daha etkileşimli):
```powershell
python .\ursina_main.py
```
Not: `ursina_main.py` artık ana menü, dünyalar listesi, dünya oluşturma ve oyuna girme akışını içerir. ESC ile menüye dönebilirsiniz. Texture atlas `textures/blocks.png` varsa dünyaya uygulanır.
```
