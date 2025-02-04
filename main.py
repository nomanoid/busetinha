import flet as ft
import yt_dlp
import re
import asyncio
import aiohttp

class VideoDownloader:
    def __init__(self):
        self.base_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]',
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'extract_flat': False,
        }

    def _detect_platform(self, url):
        url = url.lower()
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'YouTube'
        elif 'instagram.com' in url:
            return 'Instagram'
        elif 'facebook.com' in url or 'fb.watch' in url:
            return 'Facebook'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'Twitter'
        return None

    def validate_url(self, url):
        if not url:
            return False
        url = url.lower()
        pattern = r'(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|facebook\.com|fb\.watch|twitter\.com|x\.com|instagram\.com)\/\S+'
        return bool(re.match(pattern, url))

    async def get_video_info(self, url):
        try:
            platform = self._detect_platform(url)
            if not platform:
                return {'error': 'URL não suportada'}

            ydl_opts = {**self.base_opts}
            
            async with aiohttp.ClientSession() as session:
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = await asyncio.get_event_loop().run_in_executor(
                            None, lambda: ydl.extract_info(url, download=False)
                        )
                        
                        if not info:
                            return {'error': 'Não foi possível obter informações do vídeo'}

                        return {
                            'title': info.get('title', 'Unknown'),
                            'thumbnail': info.get('thumbnail'),
                            'duration': info.get('duration'),
                            'platform': platform,
                            'url': info.get('url'),
                            'webpage_url': info.get('webpage_url'),
                        }
                except Exception as e:
                    return {'error': f'Erro ao processar vídeo: {str(e)}'}

        except Exception as e:
            return {'error': f'Erro ao processar vídeo: {str(e)}'}

    async def get_direct_url(self, url):
        try:
            ydl_opts = {**self.base_opts}
            
            async with aiohttp.ClientSession() as session:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: ydl.extract_info(url, download=False)
                    )
                    
                    if not info:
                        return None, 'Não foi possível obter informações do vídeo'

                    # Tenta obter a URL direta
                    video_url = info.get('url')
                    if video_url:
                        return video_url, None

                    # Se não encontrar URL direta, procura nos formatos
                    formats = info.get('formats', [])
                    for f in reversed(formats):  # Começa dos melhores formatos
                        if f.get('url'):
                            return f['url'], None

                    return None, 'Não foi possível obter o link do vídeo'

        except Exception as e:
            return None, str(e)

def main(page: ft.Page):
    page.title = "Busetinha Downloader"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 600
    page.window_min_width = 300
    page.window_height = 800
    page.window_min_height = 600
    page.padding = 20
    page.spacing = 10
    
    if page.web:
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.scroll = ft.ScrollMode.ADAPTIVE

    async def on_url_submit(e):
        if not url_field.value:
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Por favor, insira um URL"))
            )
            return
        
        progress_ring.visible = True
        video_info_container.visible = False
        page.update()

        try:
            downloader = VideoDownloader()
            info = await downloader.get_video_info(url_field.value)

            if 'error' in info:
                page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(f"Erro: {info['error']}"))
                )
                progress_ring.visible = False
                page.update()
                return

            video_info_container.content = ft.Column(
                controls=[
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Image(
                                        src=info['thumbnail'],
                                        fit=ft.ImageFit.CONTAIN,
                                        border_radius=10,
                                        height=200,
                                    ),
                                    ft.Text(
                                        info['title'],
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Text(
                                        f"Plataforma: {info['platform']}",
                                        size=16,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Divider(),
                                    ft.ElevatedButton(
                                        "Baixar Vídeo",
                                        on_click=lambda _, url=url_field.value: asyncio.run(iniciar_download(url)),
                                        width=300,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=10,
                            ),
                            padding=20,
                        )
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
            
            progress_ring.visible = False
            video_info_container.visible = True
            page.update()
            
        except Exception as e:
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Erro ao processar vídeo: {str(e)}"))
            )
            progress_ring.visible = False
            page.update()

    async def iniciar_download(url):
        try:
            progress_ring.visible = True
            page.update()

            downloader = VideoDownloader()
            video_url, error = await downloader.get_direct_url(url)

            progress_ring.visible = False
            page.update()

            if error:
                page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Erro: {error}")))
                return

            # Abre o vídeo em uma nova aba
            page.launch_url(video_url, web_window_name="_blank")
            page.show_snack_bar(ft.SnackBar(content=ft.Text("Download iniciado!")))

        except Exception as e:
            progress_ring.visible = False
            page.update()
            page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Erro ao baixar: {str(e)}")))

    url_field = ft.TextField(
        label="Cole o link do vídeo aqui",
        width=300,
        on_submit=lambda e: asyncio.run(on_url_submit(e)),
    )
    
    progress_ring = ft.ProgressRing(visible=False)
    video_info_container = ft.Container(visible=False)

    page.add(
        ft.Column(
            [
                ft.Text(
                    "Busetinha Downloader",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "YouTube, Facebook, Twitter(X), Instagram",
                    size=16,
                    color=ft.colors.BLUE_400,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(),
                url_field,
                ft.ElevatedButton(
                    "Analisar vídeo",
                    on_click=lambda e: asyncio.run(on_url_submit(e)),
                    width=200,
                ),
                progress_ring,
                video_info_container,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        )
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER)
