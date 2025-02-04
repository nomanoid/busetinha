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
            'no_color': True,
            'extract_flat': False,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            }
        }
        
        self.platform_opts = {
            'YouTube': {
                'format': 'best',
            },
            'Instagram': {
                'format': 'best',
                'add_headers': {
                    'Accept': '*/*',
                    'X-IG-App-ID': '936619743392459',
                    'X-ASBD-ID': '198387',
                    'X-IG-WWW-Claim': '0',
                    'Origin': 'https://www.instagram.com',
                    'Referer': 'https://www.instagram.com/',
                    'X-Requested-With': 'XMLHttpRequest',
                },
            },
            'Facebook': {
                'format': 'best',
            },
            'Twitter': {
                'format': 'best',
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
                platform_headers = self.platform_opts[platform].get('add_headers', {})
                ydl_opts['http_headers'].update(platform_headers)
                
                for key, value in self.platform_opts[platform].items():
                    if key != 'add_headers':
                        ydl_opts[key] = value

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        return {'error': 'Não foi possível obter informações do vídeo'}

                    filesize = None
                    if 'filesize' in info:
                        filesize = info['filesize']
                    elif 'filesize_approx' in info:
                        filesize = info['filesize_approx']
                    elif 'formats' in info:
                        max_size = 0
                        for f in info['formats']:
                            if f.get('filesize'):
                                max_size = max(max_size, f['filesize'])
                            elif f.get('filesize_approx'):
                                max_size = max(max_size, f['filesize_approx'])
                        if max_size > 0:
                            filesize = max_size

                    size_text = 'N/A'
                    if filesize:
                        if filesize < 1024:
                            size_text = f"{filesize} B"
                        elif filesize < 1024 * 1024:
                            size_text = f"{filesize/1024:.1f} KB"
                        else:
                            size_text = f"{filesize/(1024*1024):.1f} MB"

                    formats = []
                    formats.append({
                        'format_id': 'best',
                        'quality': 'Melhor qualidade',
                        'size': size_text,
                        'url': info.get('url', None)  # Armazena a URL direta
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
        except Exception as e:
            return {'error': f'Erro ao processar vídeo: {str(e)}'}

    def download_video(self, url, format_id):
        try:
            platform = self._detect_platform(url)
            if not platform:
                return False, 'Plataforma não suportada.'

            ydl_opts = {**self.base_opts}
            if platform in self.platform_opts:
                platform_headers = self.platform_opts[platform].get('add_headers', {})
                ydl_opts['http_headers'].update(platform_headers)
                
                for key, value in self.platform_opts[platform].items():
                    if key != 'add_headers':
                        ydl_opts[key] = value

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return False, 'Não foi possível obter informações do vídeo'

                # Tenta obter a URL direta do vídeo
                direct_url = None
                
                # Primeiro tenta a URL direta do vídeo
                if 'url' in info:
                    direct_url = info['url']
                # Se não encontrar, procura nos formatos
                elif 'formats' in info:
                    formats = info['formats']
                    # Começa do formato com melhor qualidade
                    for format in reversed(formats):
                        if format.get('url'):
                            direct_url = format['url']
                            break

                if direct_url:
                    return True, direct_url
                return False, 'Não foi possível obter o link do vídeo'

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
                                    *[
                                        ft.ElevatedButton(
                                            f"Download {f['quality']} - {f['size']}" if f['size'] != 'N/A' else f"Download {f['quality']}",
                                            on_click=lambda _, url=url_field.value, format_id=f['format_id']: iniciar_download(url, format_id),
                                            width=300,
                                        )
                                        for f in info['formats']
                                    ],
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
            downloader = VideoDownloader()
            success, result = downloader.download_video(url, format_id)

            if not success:
                page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Erro: {result}")))
                return

            # Cria um link <a> para download
            download_link = ft.Text(
                "Se o download não iniciar automaticamente, clique aqui",
                color=ft.colors.BLUE,
                weight=ft.FontWeight.BOLD,
            )
            download_link.on_click = lambda _: page.launch_url(result)

            # Mostra o diálogo com o link
            page.dialog = ft.AlertDialog(
                title=ft.Text("Download"),
                content=ft.Column([
                    ft.Text("Seu download está pronto!"),
                    download_link,
                ]),
                actions=[
                    ft.TextButton("Fechar", on_click=lambda _: close_dialog())
                ],
            )
            page.dialog.open = True
            page.update()

            # Tenta iniciar o download automaticamente
            page.launch_url(result)

        except Exception as e:
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
