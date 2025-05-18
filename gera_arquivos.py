import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# Lista de 10 cores e mapeamento para códigos e cores
colors = [
    "Blue", "Red", "Green", "Orange", "Purple",
    "Yellow", "Brown", "Pink", "Gray", "Black"
]
color_to_code = {c: idx + 1 for idx, c in enumerate(colors)}
code_to_color = {v: k for k, v in color_to_code.items()}

class App:
    def __init__(self, master):
        self.master = master
        master.title("Gerador de Arquivos de Metrô")

        # === Top: número de estações e carregar ===
        frame_top = ttk.Frame(master)
        frame_top.pack(padx=10, pady=5, fill='x')
        ttk.Label(frame_top, text="Número de estações:").pack(side='left')
        self.entry_n = ttk.Entry(frame_top, width=5)
        self.entry_n.pack(side='left', padx=5)
        ttk.Button(frame_top, text="Iniciar", command=self.iniciar).pack(side='left', padx=5)
        ttk.Button(frame_top, text="Carregar", command=self.carregar).pack(side='left', padx=5)
        
        # Campo para nome da estação
        ttk.Label(frame_top, text="Nome da Estação (para A):").pack(side='left', padx=(20,0))
        self.entry_nome = ttk.Entry(frame_top, width=15)
        self.entry_nome.pack(side='left', padx=5)
        ttk.Button(frame_top, text="Salvar Nome", command=self.salvar_nome).pack(side='left', padx=5)

        # Botões de criação e remoção de estação selecionada por spinbox A
        ttk.Button(frame_top, text="Adicionar Estação", command=self.adicionar_estacao).pack(side='right', padx=5)
        ttk.Button(frame_top, text="Remover Estação Selecionada (A)", command=self.remover_estacao).pack(side='right', padx=5)

        # === Middle: conexões ===
        frame_mid = ttk.Frame(master)
        frame_mid.pack(padx=10, pady=5, fill='x')
        ttk.Label(frame_mid, text="Estação A:").grid(row=0, column=0)
        self.spin_a = tk.Spinbox(frame_mid, from_=1, to=1, width=5)
        self.spin_a.grid(row=0, column=1, padx=5)
        ttk.Label(frame_mid, text="Estação B:").grid(row=0, column=2)
        self.spin_b = tk.Spinbox(frame_mid, from_=1, to=1, width=5)
        self.spin_b.grid(row=0, column=3, padx=5)
        ttk.Label(frame_mid, text="Distância:").grid(row=0, column=4)
        self.entry_dist = ttk.Entry(frame_mid, width=7)
        self.entry_dist.grid(row=0, column=5, padx=5)
        ttk.Label(frame_mid, text="Linha:").grid(row=0, column=6)
        self.combo_line = ttk.Combobox(frame_mid, values=colors, state="readonly", width=8)
        self.combo_line.grid(row=0, column=7, padx=5)
        ttk.Button(frame_mid, text="Adicionar/Atualizar Conexão", command=self.adicionar).grid(row=0, column=8, padx=5)

        # === Treeview com conexões ===
        self.tree = ttk.Treeview(master, columns=("A","B","Dist","Line"), show='headings', height=8)
        for col, text in [("A","A"),("B","B"),("Dist","Distância"),("Line","Linha")]:
            self.tree.heading(col, text=text)
        self.tree.pack(padx=10, pady=5, fill='both', expand=True)

        # === Preview grafo ===
        self.preview_frame = ttk.Frame(master)
        self.preview_frame.pack(padx=10, pady=5, fill='both', expand=True)
        self.fig, self.ax = plt.subplots(figsize=(5,4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.preview_frame)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')

        # === Bottom: remover conexão e salvar arquivos ===
        frame_bot = ttk.Frame(master)
        frame_bot.pack(padx=10, pady=5, fill='x')
        ttk.Button(frame_bot, text="Remover Conexão", command=self.remover).pack(side='right', padx=5)
        ttk.Button(frame_bot, text="Salvar Arquivos", command=self.salvar).pack(side='right')

        # Estado interno
        self.connections = []  # (u,v,dist,code)
        self.N = 0
        self.station_names = {}  # número->nome

    def iniciar(self):
        try:
            self.N = int(self.entry_n.get())
            if self.N < 1: raise ValueError
        except:
            messagebox.showerror("Erro","Número de estações inválido"); return
        for i in range(1,self.N+1):
            self.station_names.setdefault(i,f"E{i}")
        self.atualizar_spinboxes()
        self.connections.clear(); self.tree.delete(*self.tree.get_children()); self.update_preview()
        messagebox.showinfo("Info",f"Configurado para {self.N} estações")

    def carregar(self):
        files = ["estacoes.txt","distancias.txt","linhas.txt","nomes_estacoes.txt"]
        missing = [f for f in files if not os.path.exists(f)]
        if missing:
            messagebox.showerror("Erro",f"Arquivos faltando: {', '.join(missing)}"); return
        dist = np.loadtxt("distancias.txt")
        lin = np.loadtxt("linhas.txt")
        grafo = {}
        with open("estacoes.txt","r") as f:
            for ln in f:
                est,con = ln.strip().split('-')
                viz = con.split(' ') if con else []
                grafo[int(est)] = [int(v) for v in viz if v]
        self.station_names = {}
        with open("nomes_estacoes.txt","r") as f:
            for ln in f:
                num,name = ln.strip().split('-',1)
                self.station_names[int(num)] = name
        self.N = len(grafo)
        self.entry_n.delete(0,tk.END); self.entry_n.insert(0,str(self.N))
        self.atualizar_spinboxes(); self.connections.clear(); self.tree.delete(*self.tree.get_children())
        for u,vs in grafo.items():
            for v in vs:
                if u<v:
                    d = float(dist[u-1,v-1]); c = int(lin[u-1,v-1])
                    self.connections.append((u,v,d,c))
                    self.tree.insert("","end",values=(u,v,d,code_to_color.get(c,'Black')))
        self.update_preview(); messagebox.showinfo("Info","Arquivos carregados com sucesso")

    def salvar_nome(self):
        try:
            u = int(self.spin_a.get()); name = self.entry_nome.get().strip()
            if not name: raise ValueError("Nome vazio")
            self.station_names[u] = name
            messagebox.showinfo("Info",f"Nome da estação {u} salvo")
        except Exception as e:
            messagebox.showerror("Erro",str(e))

    def adicionar(self):
        try:
            a = int(self.spin_a.get()); b = int(self.spin_b.get())
            if a==b: raise ValueError("Estações iguais")
            d = float(self.entry_dist.get()); line = self.combo_line.get()
            if not line: raise ValueError("Linha não selecionada")
        except Exception as e:
            messagebox.showerror("Erro",str(e)); return
        u,v = sorted((a,b)); code = color_to_code[line]; updated=False
        for idx,(u0,v0,_,_) in enumerate(self.connections):
            if u0==u and v0==v:
                self.connections[idx] = (u,v,d,code); updated=True
                for it in self.tree.get_children():
                    vals = self.tree.item(it,'values')
                    if int(vals[0])==u and int(vals[1])==v:
                        self.tree.item(it,values=(u,v,d,line)); break
                break
        if not updated:
            self.connections.append((u,v,d,code))
            self.tree.insert("","end",values=(u,v,d,line))
        self.update_preview()

    def remover(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("Aviso","Selecione conexão"); return
        for it in sel:
            u,v = map(int,self.tree.item(it,'values')[:2])
            self.connections = [c for c in self.connections if not(c[0]==u and c[1]==v)]
            self.tree.delete(it)
        self.update_preview()

    def adicionar_estacao(self):
        self.N += 1; self.station_names[self.N] = f"E{self.N}"
        self.entry_n.delete(0,tk.END); self.entry_n.insert(0,str(self.N))
        self.atualizar_spinboxes()
        messagebox.showinfo("Info",f"Estação {self.N} adicionada")
        self.update_preview()

    def remover_estacao(self):
        try:
            u = int(self.spin_a.get())
            if u<1 or u>self.N: raise ValueError
        except:
            messagebox.showerror("Erro","Selecione estação válida (A)"); return
        self.connections = [(x,y,d,c) for x,y,d,c in self.connections if x!=u and y!=u]
        shifted = []
        for x,y,d,c in self.connections:
            xx = x-1 if x>u else x
            yy = y-1 if y>u else y
            shifted.append((xx,yy,d,c))
        self.connections = shifted
        del self.station_names[u]
        self.station_names = {i-1 if i>u else i: n for i,n in self.station_names.items()}
        self.N -= 1
        self.entry_n.delete(0,tk.END); self.entry_n.insert(0,str(self.N))
        self.atualizar_spinboxes(); self.tree.delete(*self.tree.get_children())
        for x,y,d,c in self.connections:
            self.tree.insert("","end",values=(x,y,d,code_to_color.get(c,'Black')))
        messagebox.showinfo("Info",f"Estação {u} removida")
        self.update_preview()

    def atualizar_spinboxes(self):
        self.spin_a.config(to=self.N); self.spin_b.config(to=self.N)

    def update_preview(self):
        self.ax.clear()
        G = nx.Graph()
        G.add_nodes_from(range(1, self.N+1))
        for u, v, d, c in self.connections:
            G.add_edge(u, v, weight=d, linha=c)
        # tenta Kamada-Kawai (precisa scipy)
        try:
            pos = nx.kamada_kawai_layout(G, weight='weight')
        except (ImportError, ModuleNotFoundError):
            # fallback: usa spring_layout com peso invertido para simular distâncias
            for u,v,data in G.edges(data=True):
                data['weight_inv'] = 1.0/data['weight'] if data['weight']>0 else 1.0
            pos = nx.spring_layout(G, weight='weight_inv', seed=42)

        nx.draw_networkx_nodes(G, pos, ax=self.ax,
                               node_color='lightgray', node_size=300)
        labels = {i: self.station_names.get(i, f"E{i}") for i in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, ax=self.ax)
        for u, v, d in G.edges(data=True):
            nx.draw_networkx_edges(G, pos, [(u, v)],
                                   edge_color=code_to_color.get(d['linha'], 'black'),
                                   ax=self.ax)
        edge_labels = {(u, v): f"{d['weight']:.1f}" for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=self.ax)

        self.ax.set_title('Preview do Grafo')
        self.ax.axis('off')
        self.canvas.draw()

    def salvar(self):
        if self.N<1: messagebox.showerror("Erro","Defina estações"); return
        ests = {i:set() for i in range(1,self.N+1)}
        dist = np.zeros((self.N,self.N)); lines = np.zeros((self.N,self.N),dtype=int)
        for u,v,d,c in self.connections:
            ests[u].add(v); ests[v].add(u)
            dist[u-1,v-1] = dist[v-1,u-1] = d
            lines[u-1,v-1] = lines[v-1,u-1] = c
        with open("estacoes.txt","w") as f:
            for i in range(1,self.N+1):
                f.write(f"{i}-{' '.join(map(str,sorted(ests[i])))}\n")
        np.savetxt("distancias.txt",dist,fmt="%.1f")
        np.savetxt("linhas.txt",lines,fmt="%d")
        with open("nomes_estacoes.txt","w") as f:
            for i in range(1,self.N+1):
                f.write(f"{i}-{self.station_names.get(i,f'E{i}')}\n")
        messagebox.showinfo("Sucesso","Arquivos gerados com sucesso")

if __name__=="__main__":
    root=tk.Tk(); app=App(root); root.mainloop()
