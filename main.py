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
        
        # Configurações específicas para cada plataforma
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

            # Converte URLs se necessário
            if platform == 'Twitter' and 'x.com' in url.lower():
                url = url.replace('x.com', 'twitter.com')

            # Configurações base
            ydl_opts = {**self.base_opts}
            
            # Adiciona configurações específicas da plataforma
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

                    # Tenta obter o tamanho do arquivo de diferentes maneiras
                    filesize = None
                    if 'filesize' in info:
                        filesize = info['filesize']
                    elif 'filesize_approx' in info:
                        filesize = info['filesize_approx']
                    elif 'formats' in info:
                        # Procura o formato com maior tamanho
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
                
                formats = []
                formats.append({
                    'format_id': 'best',
                    'quality': 'Melhor qualidade',
                    'size': size_text
                })
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': info.get('duration'),
                    'platform': platform,
                    'formats': formats,
                }
        except Exception as e:
            return {'error': f'Erro ao processar vídeo: {str(e)}'}

    def download_video(self, url, format_id, output_dir=None):
        try:
            platform = self._detect_platform(url)
            if not platform:
                return False, 'Plataforma não suportada. No momento, apenas YouTube, Facebook, Twitter e Instagram são suportados.'

            ydl_opts = {**self.base_opts}
            
            # Adiciona headers específicos da plataforma
            if platform in self.platform_opts:
                platform_headers = self.platform_opts[platform].get('add_headers', {})
                ydl_opts['http_headers'].update(platform_headers)
                
                for key, value in self.platform_opts[platform].items():
                    if key != 'add_headers':
                        ydl_opts[key] = value

            if output_dir:
                # Modo desktop: salva no diretório escolhido
                ydl_opts.update({
                    'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                })
            else:
                # Modo web: retorna o URL direto do vídeo
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        return False, 'Não foi possível obter informações do vídeo'
                    
                    # Tenta obter a melhor URL do vídeo
                    video_url = None
                    if 'url' in info:
                        video_url = info['url']
                    elif 'formats' in info and len(info['formats']) > 0:
                        # Pega o formato com melhor qualidade
                        best_format = info['formats'][-1]
                        video_url = best_format.get('url')
                    
                    if video_url:
                        return True, video_url
                    return False, 'Não foi possível obter o URL do vídeo'

            if output_dir:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    error_code = ydl.download([url])
                    if error_code != 0:
                        return False, 'Erro ao baixar o vídeo'
                return True, None

        except Exception as e:
            return False, str(e)

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
                                            on_click=lambda _, url=url_field.value, format_id=f['format_id']: download_video(url, format_id),
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

    def download_video(url, format_id):
        try:
            downloader = VideoDownloader()
            success, result = downloader.download_video(url, format_id)

            if not success:
                page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(f"Erro: {result}"))
                )
                return

            # Cria um link para download direto
            page.launch_url(result)
            
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Download iniciado!"))
            )
        except Exception as e:
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Erro ao iniciar download: {str(e)}"))
            )

    # Interface principal
    url_field = ft.TextField(
        label="Cole o link do vídeo aqui",
        width=300,
        on_submit=on_url_submit,
    )
    
    progress_ring = ft.ProgressRing(visible=False)
    
    video_info_container = ft.Container(
        visible=False,
    )

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
