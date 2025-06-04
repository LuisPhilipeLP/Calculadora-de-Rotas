import os
import sys
import time
import csv
import threading
import subprocess
import tkinter as tk
from tkinter import PhotoImage, messagebox, ttk

import openrouteservice


API_KEY = "5b3ce3597851110001cf6248b84f867b510e48328a2259a694fcb319"
client = openrouteservice.Client(key=API_KEY)

# Ponto fixo (longitude, latitude)
location_A = (-43.180270812085745, -19.848380041135304)



# === Função auxiliar para obter caminho do executável ou do script ===
def resource_path(relative_path):
    """Resolve o caminho para quando for usado no PyInstaller (one-dir ou one-file)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Função unica
def abrir_rota_unica():
    bairros_dict = {}
    with open("bairros.txt", encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 3:
                bairro = row[0].strip()
                try:
                    lng = float(row[1].strip())
                    lat = float(row[2].strip())
                    bairros_dict[bairro] = (lng, lat)
                except ValueError:
                    continue

    def abrir_menu_principal():
        janela.deiconify()
        unica.after(0, unica.destroy)
        janela.state('zoomed')



    # Efeitos de hover para o botão voltar
    def on_enter_voltar(event):
        botao_voltar.config(cursor="hand2", bg="#035efc", relief="raised")

    def on_leave_voltar(event):
        botao_voltar.config(cursor="arrow", bg="#33bd43", relief="flat")

    def get_travel_time(origin, destination):
        route = client.directions(
            coordinates=[origin, destination],
            profile='driving-car',
            format='geojson'
        )
        duration_sec = route['features'][0]['properties']['summary']['duration']
        return duration_sec / 60  # minutos

    def calcular_rota_thread(bairro):
        try:
            tempo_ida = get_travel_time(location_A, bairros_dict[bairro])
            tempo_volta = get_travel_time(bairros_dict[bairro], location_A)
            total = tempo_ida + tempo_volta

            resultado_texto = (f"\nFast Food da Val → {bairro}\n"
                              f"🛵 Ida: {tempo_ida:.1f} minutos\n\n"
                              f"{bairro} → Fast Food da Val\n"
                              f"🔁 Volta: {tempo_volta:.1f} minutos\n\n"
                              f"⏱️ Total estimado: {total:.1f} minutos")

            # Atualiza resultado na thread principal
            unica.after(0, mostrar_resultado, resultado_texto)
        except openrouteservice.exceptions.ApiError as e:
            unica.after(0, lambda: messagebox.showerror("Erro de rota", str(e)))
        finally:
            unica.after(0, esconder_loading)

    def mostrar_resultado(texto):
        resultado.config(text=texto)

    def mostrar_loading():
        loading_label.pack(pady=(0, 20))
        animate_loading(0)

    def esconder_loading():
        loading_label.pack_forget()

    def animate_loading(count):
        dots = '.' * (count % 4)
        loading_label.config(text=f"Calculando rota{dots}")
        if loading_label.winfo_ismapped():
            unica.after(500, animate_loading, count + 1)

    def calcular_rota(event=None):
        bairro = combo.get()
        if bairro not in bairros_dict:
            messagebox.showerror("Erro", "Bairro não encontrado.")
            return

        resultado.config(text="")
        mostrar_loading()

        # Thread para não travar interface
        thread = threading.Thread(target=calcular_rota_thread, args=(bairro,), daemon=True)
        thread.start()

    class AutocompleteCombobox(ttk.Combobox):
        def set_completion_list(self, completion_list):
            self._completion_list = sorted(completion_list, key=str.lower)
            self._hits = []
            self._hit_index = 0
            self.position = 0
            self.bind('<KeyRelease>', self.handle_keyrelease)
            self.bind('<Return>', self.select_suggestion)
            self['values'] = self._completion_list

        def autocomplete(self, delta=0):
            if delta:
                self.position = len(self.get())
            else:
                self.position = self.index(tk.END)

            _hits = [elem for elem in self._completion_list if elem.lower().startswith(self.get().lower())]

            if _hits != self._hits:
                self._hit_index = 0
                self._hits = _hits

            if _hits:
                self.delete(0, tk.END)
                self.insert(0, _hits[self._hit_index])
                self.select_range(self.position, tk.END)

        def handle_keyrelease(self, event):
            if event.keysym in ("BackSpace", "Left"):
                self.position = self.index(tk.END)
            elif len(event.keysym) == 1 or event.keysym == "Right":
                self.autocomplete()

        def select_suggestion(self, event):
            if self._hits:
                self.delete(0, tk.END)
                self.insert(0, self._hits[self._hit_index])
            calcular_rota()

    def rgb_to_hex(rgb):
        return "#%02x%02x%02x" % rgb

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2 ,4))

    def fade_color(widget, start_color, end_color, steps=10, delay=30):
        start_rgb = hex_to_rgb(start_color)
        end_rgb = hex_to_rgb(end_color)
        diff = [(e - s)/steps for s,e in zip(start_rgb, end_rgb)]

        def step(i=0):
            if i > steps:
                return
            new_color = [int(s + diff[j]*i) for j,s in enumerate(start_rgb)]
            widget.config(bg=rgb_to_hex(tuple(new_color)))
            widget.after(delay, step, i+1)

        step()

    unica = tk.Toplevel(janela)
    unica.title("Calculadora de Rota única - Fast Food da Val")
    # Obtém a resolução da tela

    # Calcula dimensões 
    unica.minsize(600, 800)
    unica.state("zoomed")
    unica.configure(bg="#021e4f")
    unica.wm_attributes('-alpha', 0.98)  # 98% opaco

    #unica.iconbitmap(resource_path("icone.ico"))





    frame_borda = tk.Frame(unica, bg="white", bd=4, relief="solid")
    frame_borda.place(relx=0.5, rely=0.5, anchor="center")

    frame = tk.Frame(frame_borda, bg="white")
    frame.pack(padx=10, pady=10)

    try:
        fonte_titulo = ("Segoe UI Semibold", 18)
        fonte_normal = ("Segoe UI", 14)
    except:
        fonte_titulo = ("Arial", 18)
        fonte_normal = ("Arial", 14)

    label_instrucao = tk.Label(frame, text="Escolha o bairro de destino:", font=fonte_titulo, bg="white", fg="#000000")
    label_instrucao.pack(pady=(0, 20))

    combo = AutocompleteCombobox(frame, font=fonte_normal, width=30, justify="center")
    combo.set_completion_list(list(bairros_dict.keys()))
    combo.pack(pady=(0, 20))

    cor_normal = "#33bd43"
    cor_hover = "#035efc"
    texto_normal = "white"

    def on_enter(event):
        botao.config(cursor="hand2", bg=cor_hover, relief="raised")

    def on_leave(event):
        botao.config(cursor="arrow", bg=cor_normal, relief="flat")

    botao = tk.Button(frame, text="Calcular Rota", command=calcular_rota,
                      font=fonte_normal, width=20, height=1,
                      bg=cor_normal, fg=texto_normal, relief="flat", borderwidth=0)
    botao.pack(pady=(0, 25))
    botao.bind("<Enter>", on_enter)
    botao.bind("<Leave>", on_leave)

    # Botão "Voltar ao menu principal" no canto inferior esquerdo
    botao_voltar = tk.Button(unica, text="← Voltar ao Menu", font=cor_normal, width=20, height=2,
                             bg="#33bd43", fg="white", relief="flat", borderwidth=0,
                             command=abrir_menu_principal)
    botao_voltar.place(x=20, rely=0.95, anchor='sw')  # Fixa no canto inferior esquerdo

    botao_voltar.bind("<Enter>", on_enter_voltar)
    botao_voltar.bind("<Leave>", on_leave_voltar)


    loading_label = tk.Label(frame, text="Calculando rota", font=fonte_normal, bg="white", fg="#000000")
    # Não aparece na inicialização, só durante cálculo

    resultado = tk.Label(frame, text="", font=fonte_normal, bg="white", fg="#000000", justify="center")
    resultado.pack(pady=(10, 10))


    def on_close():
        janela.destroy()  # closes both windows, ends app

    unica.protocol("WM_DELETE_WINDOW", on_close)

    janela.withdraw()
    unica.mainloop()

   
# Fim da função única

# Função Agrupada
def abrir_rota_agrupada():
    bairros_dict = {}
    with open("bairros.txt", encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 3:
                bairro = row[0].strip()
                try:
                    lng = float(row[1].strip())
                    lat = float(row[2].strip())
                    bairros_dict[bairro] = (lng, lat)
                except ValueError:
                    continue

    # === CACHE DE ROTAS ===
    CACHE_FILE = "rotas_cache.csv"
    cache_rotas = {}

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 3:
                    try:
                        origem = eval(row[0])
                        destino = eval(row[1])
                        tempo = float(row[2])
                        cache_rotas[(origem, destino)] = tempo
                    except:
                        continue

    def abrir_menu_principal():
        janela.deiconify()
        agrupada.after(0, agrupada.destroy)
        janela.state('zoomed')

    # Efeitos de hover para o botão voltar
    def on_enter_voltar(event):
        botao_voltar.config(cursor="hand2", bg="#035efc", relief="raised")

    def on_leave_voltar(event):
        botao_voltar.config(cursor="arrow", bg="#33bd43", relief="flat")    

    def salvar_no_cache(origem, destino, tempo):
        cache_rotas[(origem, destino)] = tempo
        with open(CACHE_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([str(origem), str(destino), tempo])

    def get_travel_time(origem, destino):
        if (origem, destino) in cache_rotas:
            return cache_rotas[(origem, destino)]
        elif (destino, origem) in cache_rotas:
            return cache_rotas[(destino, origem)]

        try:
            route = client.directions(
                coordinates=[origem, destino],
                profile='driving-car',
                format='geojson'
            )
            duration_sec = route['features'][0]['properties']['summary']['duration']
            tempo_min = duration_sec / 60
            salvar_no_cache(origem, destino, tempo_min)
            return tempo_min
        except openrouteservice.exceptions.ApiError as e:
            raise e

    # === FUNÇÕES DE ROTA ===
    def nearest_neighbor_route(start, points):
        unvisited = points.copy()
        route = [start]
        current = start
        while unvisited:
            nearest = min(unvisited, key=lambda point: get_travel_time(current, point))
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        route.append(start)
        return route

    def calcular_rota_thread(bairros_selecionados):
        try:
            coordenadas = [bairros_dict[bairro] for bairro in bairros_selecionados]
            rota_coords = nearest_neighbor_route(location_A, coordenadas)

            resultado_texto = "\nRota Calculada:\n"
            total_tempo = 0.0
            for i in range(len(rota_coords) - 1):
                origem = rota_coords[i]
                destino = rota_coords[i + 1]
                tempo = get_travel_time(origem, destino)
                total_tempo += tempo

                origem_nome = "Fast Food da Val" if origem == location_A else next((nome for nome, coord in bairros_dict.items() if coord == origem), "Desconhecido")
                destino_nome = "Fast Food da Val" if destino == location_A else next((nome for nome, coord in bairros_dict.items() if coord == destino), "Desconhecido")

                resultado_texto += f"{origem_nome} → {destino_nome}: {tempo:.1f} minutos\n"

            resultado_texto += f"\n⏱️ Tempo total estimado: {total_tempo:.1f} minutos"
            agrupada.after(0, mostrar_resultado, resultado_texto)
        except openrouteservice.exceptions.ApiError as e:
            agrupada.after(0, lambda: messagebox.showerror("Erro de rota", str(e)))
        finally:
            agrupada.after(0, esconder_loading)

    # === INTERFACE ===
    def mostrar_resultado(texto):
        resultado.config(text=texto)

    def mostrar_loading():
        loading_label.pack(pady=(0, 20))
        animate_loading(0)

    def esconder_loading():
        loading_label.pack_forget()

    def animate_loading(count):
        dots = '.' * (count % 4)
        loading_label.config(text=f"Calculando rota{dots}")
        if loading_label.winfo_ismapped():
            agrupada.after(500, animate_loading, count + 1)

    def calcular_rota(event=None):
        selecoes = listbox.curselection()
        if not selecoes:
            messagebox.showerror("Erro", "Selecione pelo menos um bairro.")
            return

        bairros_selecionados = [listbox.get(i) for i in selecoes]

        resultado.config(text="")
        mostrar_loading()

        thread = threading.Thread(target=calcular_rota_thread, args=(bairros_selecionados,), daemon=True)
        thread.start()

    agrupada = tk.Toplevel(janela)

    # Obtém a resolução da tela
    largura_tela = agrupada.winfo_screenwidth()
    altura_tela = int(agrupada.winfo_screenheight())
    # Calcula dimensões 
    altura_agrupada = int(altura_tela -200)
    largura_agrupada = int(altura_tela * (9/16))
    agrupada.minsize(450, 600)
    agrupada.state("zoomed")


    # Define o tamanho e posição da agrupada
    agrupada.geometry(f"{largura_agrupada}x{altura_agrupada}")

    agrupada.title("Calculadora de Rota Agrupada - Fast Food da Val")
    agrupada.configure(bg="#021e4f")
    agrupada.wm_attributes('-alpha', 0.98)
    #agrupada.iconbitmap(resource_path("icone.ico"))

    frame_borda = tk.Frame(agrupada, bg="white", bd=4, relief="solid")
    frame_borda.place(relx=0.5, rely=0.5, anchor="center")

    frame = tk.Frame(frame_borda, bg="white")
    frame.pack(padx=10, pady=10)

    try:
        fonte_titulo = ("Segoe UI Semibold", 18)
        fonte_normal = ("Segoe UI", 14)
    except:
        fonte_titulo = ("Arial", 18)
        fonte_normal = ("Arial", 14)

    label_instrucao = tk.Label(frame, text="Selecione os bairros de destino:", font=fonte_titulo, bg="white", fg="#000000")
    label_instrucao.pack(pady=(0, 20))

    listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, font=fonte_normal, width=30, height=10)
    for bairro in bairros_dict.keys():
        listbox.insert(tk.END, bairro)
    listbox.pack(pady=(0, 20))

    cor_normal = "#33bd43"
    cor_hover = "#035efc"
    texto_normal = "white"

    def on_enter(event):
        botao.config(cursor="hand2", bg=cor_hover, relief="raised")

    def on_leave(event):
        botao.config(cursor="arrow", bg=cor_normal, relief="flat")

    botao = tk.Button(frame, text="Calcular Rota", command=calcular_rota,
                      font=fonte_normal, width=20, height=1,
                      bg=cor_normal, fg=texto_normal, relief="flat", borderwidth=0)
    botao.pack(pady=(0, 25))
    botao.bind("<Enter>", on_enter)
    botao.bind("<Leave>", on_leave)

    # Botão "Voltar ao menu principal" no canto inferior esquerdo
    botao_voltar = tk.Button(agrupada, text="← Voltar ao Menu", font=cor_normal, width=20, height=2,
                             bg="#33bd43", fg="white", relief="flat", borderwidth=0,
                             command=abrir_menu_principal)
    botao_voltar.place(x=20, rely=0.95, anchor='sw')  # Fixa no canto inferior esquerdo

    botao_voltar.bind("<Enter>", on_enter_voltar)
    botao_voltar.bind("<Leave>", on_leave_voltar)

    loading_label = tk.Label(frame, text="Calculando rota", font=fonte_normal, bg="white", fg="#000000")

    resultado = tk.Label(frame, text="", font=fonte_normal, bg="white", fg="#000000", justify="left")
    resultado.pack(pady=(10, 10))


    def on_close():
        janela.destroy()  # closes both windows, ends app

    agrupada.protocol("WM_DELETE_WINDOW", on_close)


    janela.withdraw()

    agrupada.mainloop()
# Fim da Função Agrupada


# Funções de hover
def on_enter_unica(event):
    botao_unica.config(bg="#035efc", cursor="hand2")

def on_leave_unica(event):
    botao_unica.config(bg="#33bd43", cursor="arrow")

def on_enter_agrupada(event):
    botao_agrupada.config(bg="#035efc", cursor="hand2")

def on_leave_agrupada(event):
    botao_agrupada.config(bg="#33bd43", cursor="arrow")

# Criar janela principal
janela = tk.Tk()
janela.title("Calculadora de Rotas - Fast Food da Val")

janela.minsize(450, 600)
janela.state("zoomed")
janela.configure(bg="#021e4f")

# Ícone
#icone_path = resource_path("icone.ico")
#if os.path.exists(icone_path):
#    janela.iconbitmap(icone_path)
icon_img = tk.PhotoImage(file=resource_path("icone.png"))
janela.wm_iconphoto(True, icon_img)

fonte_titulo = ("Segoe UI Semibold", 20)
fonte_botao = ("Segoe UI", 14)

# Frame
frame_borda = tk.Frame(janela, bg="white", bd=4, relief="solid")
frame_borda.place(relx=0.5, rely=0.5, anchor="center")

frame_conteudo = tk.Frame(frame_borda, bg="white")
frame_conteudo.pack(padx=30, pady=30)

# Imagem
try:
    imagem_path = resource_path("imagem.png")
    imagem = PhotoImage(file=imagem_path)
    label_imagem = tk.Label(frame_conteudo, image=imagem, bg="white")
    label_imagem.pack(pady=(0, 20))
except Exception as e:
    print("Erro ao carregar a imagem:", e)

# Título
titulo = tk.Label(frame_conteudo, text="Escolha o tipo de rota", font=fonte_titulo, bg="white", fg="#000000")
titulo.pack(pady=(0, 40))

# Botões
botao_unica = tk.Button(frame_conteudo, text="Rota Única", font=fonte_botao, width=20, height=2,
                        bg="#33bd43", fg="white", relief="flat", borderwidth=0, command=abrir_rota_unica)
botao_unica.pack(pady=10)
botao_unica.bind("<Enter>", on_enter_unica)
botao_unica.bind("<Leave>", on_leave_unica)

botao_agrupada = tk.Button(frame_conteudo, text="Rotas Agrupadas", font=fonte_botao, width=20, height=2,
                           bg="#33bd43", fg="white", relief="flat", borderwidth=0, command=abrir_rota_agrupada)
botao_agrupada.pack(pady=10)
botao_agrupada.bind("<Enter>", on_enter_agrupada)
botao_agrupada.bind("<Leave>", on_leave_agrupada)

janela.mainloop()
