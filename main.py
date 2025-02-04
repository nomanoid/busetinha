import flet as ft
from flet import Colors, Icons
import yt_dlp
import requests
from PIL import Image
from io import BytesIO
import os
import re
import json

class VideoDownloader:
    def __init__(self):
        self.base_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'merge_output_format': 'mp4',
            'ignoreerrors': True,
            'extract_flat': False,
            'socket_timeout': 30,
            'no_check_certificate': True,  # Importante para o Render
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
        }
        
        self.platform_opts = {
            'YouTube': {
                'format': 'best',
                'nocheckcertificate': True,
            },
            'Instagram': {
                'format': 'best',
                'nocheckcertificate': True,
            },
            'Facebook': {
                'format': 'best',
                'nocheckcertificate': True,
            },
            'Twitter': {
                'format': 'best',
                'nocheckcertificate': True,
            }
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
            if 'x.com' in url:
                url = url.replace('x.com', 'twitter.com')
            return 'Twitter'
        return None

    def validate_url(self, url):
        if not url:
            return False
        url = url.lower()
        pattern = r'(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|facebook\.com|fb\.watch|twitter\.com|x\.com|instagram\.com)\/\S+'
        return bool(re.match(pattern, url))

    def get_video_info(self, url):
        try:
            platform = self._detect_platform(url)
            if not platform:
                return {'error': 'URL não suportada'}

            ydl_opts = {**self.base_opts}
            if platform in self.platform_opts:
                ydl_opts.update(self.platform_opts[platform])

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        return {'error': 'Não foi possível obter informações do vídeo'}

                    formats = []
                    formats.append({
                        'format_id': 'best',
                        'quality': 'Melhor qualidade',
                        'size': 'N/A'
                    })
                    
                    return {
                        'title': info.get('title', 'Unknown'),
                        'thumbnail': info.get('thumbnail'),
                        'duration': info.get('duration'),
                        'platform': platform,
                        'formats': formats,
                    }

                except yt_dlp.utils.ExtractorError as e:
                    if 'Private video' in str(e):
                        return {'error': 'Este vídeo é privado'}
                    elif 'This video is not available' in str(e):
                        return {'error': 'Este vídeo não está disponível'}
                    elif 'Sign in' in str(e):
                        return {'error': 'Este conteúdo requer login'}
                    else:
                        return {'error': f'Erro ao processar vídeo: {str(e)}'}

        except Exception as e:
            return {'error': f'Erro ao processar vídeo: {str(e)}'}

    def download_video(self, url, format_id):
        try:
            platform = self._detect_platform(url)
            if not platform:
                return False, 'URL não suportada'

            ydl_opts = {**self.base_opts}
            if platform in self.platform_opts:
                ydl_opts.update(self.platform_opts[platform])

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        return False, 'Não foi possível obter informações do vídeo'

                    # Primeiro tenta pegar a URL direta do vídeo
                    if 'url' in info:
                        video_url = info['url']
                        return True, video_url

                    # Se não encontrar, procura nos formatos
                    if 'formats' in info:
                        formats = info['formats']
                        # Começa do formato com melhor qualidade
                        for format in reversed(formats):
                            if 'url' in format:
                                return True, format['url']

                    return False, 'Não foi possível obter o link do vídeo'

                except yt_dlp.utils.ExtractorError as e:
                    return False, f'Erro ao extrair vídeo: {str(e)}'

        except Exception as e:
            return False, f'Erro ao baixar vídeo: {str(e)}'

def main(page: ft.Page):
    page.title = "Busetinha Downloader"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.spacing = 10
    
    # Configurações web
    if page.web:
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.scroll = ft.ScrollMode.ADAPTIVE
        # Configurações específicas para web
        page.window_width = 600
        page.window_min_width = 300
        page.window_height = 800
        page.window_min_height = 600

    def on_url_submit(e):
        if not url_field.value:
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Por favor, insira um URL"))
            )
            return
        
        if not validate_url(url_field.value):
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("URL inválido. Por favor, insira um URL válido."))
            )
            return

        progress_ring.visible = True
        video_info_container.visible = False
        page.update()

        try:
            downloader = VideoDownloader()
            info = downloader.get_video_info(url_field.value)

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
                                    ft.Text(
                                        format_duration(info['duration']),
                                        size=16,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Divider(),
                                    ft.ElevatedButton(
                                        "Baixar Vídeo",
                                        on_click=lambda _, url=url_field.value: iniciar_download(url, 'best'),
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

    def iniciar_download(url, format_id):
        try:
            progress_ring.visible = True
            page.update()

            downloader = VideoDownloader()
            success, result = downloader.download_video(url, format_id)

            progress_ring.visible = False
            page.update()

            if not success:
                page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Erro: {result}")))
                return

            # Cria um diálogo com opções de download
            download_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Download Pronto"),
                content=ft.Column([
                    ft.Text("Escolha como deseja baixar o vídeo:"),
                    ft.ElevatedButton(
                        "Abrir em Nova Aba",
                        on_click=lambda _: open_in_new_tab(result),
                        width=200,
                    ),
                ], tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                actions=[
                    ft.TextButton("Fechar", on_click=lambda _: close_dialog()),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            def open_in_new_tab(url):
                page.launch_url(url, web_window_name="_blank")
                close_dialog()

            def close_dialog():
                page.dialog.open = False
                page.update()

            page.dialog = download_dialog
            download_dialog.open = True
            page.update()

        except Exception as e:
            progress_ring.visible = False
            page.update()
            page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Erro ao baixar: {str(e)}")))

    def close_dialog():
        page.dialog.open = False
        page.update()

    def format_duration(duration):
        if not duration:
            return "Duração não disponível"
        
        try:
            total_seconds = int(float(duration))
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"Duração: {minutes}:{seconds:02d}"
        except:
            return "Duração não disponível"

    def validate_url(url):
        if not url:
            return False
        url = url.lower()
        pattern = r'(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|facebook\.com|fb\.watch|twitter\.com|x\.com|instagram\.com)\/\S+'
        return bool(re.match(pattern, url))

    # Interface principal
    url_field = ft.TextField(
        label="Cole o link do vídeo aqui",
        width=300,
        on_submit=on_url_submit,
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
                    color=Colors.BLUE_400,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(),
                url_field,
                ft.ElevatedButton(
                    "Analisar vídeo",
                    on_click=on_url_submit,
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
