import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
import numpy as np

# ----- Construção do Grafo Dinâmico -----
def build_graph(estacoes_path, distancias_path, linhas_path):
    # Lê as estações e conexões
    with open(estacoes_path, 'r') as f:
        raw_estacoes = [line.strip() for line in f if line.strip()]
    # Carrega matrizes de distância e linha
    distancias = np.loadtxt(distancias_path)
    linhas = np.loadtxt(linhas_path)

    # Monta dicionário: estação -> lista de vizinhos
    grafo = {}
    for line in raw_estacoes:
        est, conex = line.split('-')
        viz = conex.split(' ') if conex else []
        grafo[int(est)] = [int(v) for v in viz if v]

    # Cria grafo NetworkX dinamicamente
    G = nx.Graph()
    for u in grafo:
        G.add_node(u)
    for u, vizinhos in grafo.items():
        for v in vizinhos:
            if not G.has_edge(u, v):
                peso = float(distancias[u-1, v-1])
                cod_linha = int(linhas[u-1, v-1])
                G.add_edge(u, v, weight=peso, linha=cod_linha)
    return G

# ----- Algoritmo de Dijkstra com penalidade de troca -----
def dijkstra_with_transfer(G, origem, destino, tempo_troca):
    caminho = nx.dijkstra_path(G, origem, destino, weight="weight")
    total = 0
    troca = 0
    for i in range(len(caminho) - 1):
        u, v = caminho[i], caminho[i+1]
        total += G[u][v]['weight']
        if i > 0:
            pa = caminho[i-1]
            if G[pa][u]['linha'] != G[u][v]['linha']:
                troca += 1
    return caminho, total + troca * tempo_troca, troca

# ----- Carrega grafo e configurações iniciais -----
G = build_graph('estacoes.txt', 'distancias.txt', 'linhas.txt')
N = G.number_of_nodes()
pos = nx.spring_layout(G, seed=42)
canvas_widget = None
fig, ax = None, None

# ----- Desenha o grafo e destaca o caminho -----
def desenhar_grafo_com_caminho(caminho):
    global canvas_widget, fig, ax
    ax.clear()

    # Nós e rótulos
    labels = {u: f"E{u}" for u in G.nodes()}
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=600, node_color='lightgray')
    nx.draw_networkx_labels(G, pos, labels, ax=ax)

    # Arestas sem e com destaque
    edge_labels = {(u, v): f"{d['weight']:.1f}" for u, v, d in G.edges(data=True)}
    cores = {1:'blue',2:'red',3:'green',4:'orange',0:'gray'}
    for u, v, d in G.edges(data=True):
        cor = cores.get(d['linha'], 'black')
        nx.draw_networkx_edges(G, pos, [(u, v)], edge_color=cor, ax=ax)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax)
    for i in range(len(caminho)-1):
        u, v = caminho[i], caminho[i+1]
        cor = cores.get(G[u][v]['linha'], 'black')
        nx.draw_networkx_edges(G, pos, [(u, v)], width=4, style='dashed', edge_color=cor, ax=ax)

    ax.set_title('Mapa do Metrô - Caminho Mais Rápido')
    ax.axis('off')

    # Integração com Tkinter
    if canvas_widget:
        canvas_widget.get_tk_widget().destroy()
    canvas_widget = FigureCanvasTkAgg(fig, master=fig_frame)
    canvas_widget.draw()
    canvas_widget.get_tk_widget().pack(expand=True, fill='both')

# ----- Função principal de cálculo -----
def calcular():
    try:
        o = int(origem_var.get())
        d = int(destino_var.get())
        t = float(troca_var.get())
        caminho, tempo, trocas = dijkstra_with_transfer(G, o, d, t)
        resultado = (
            f"Caminho: {' → '.join(map(str, caminho))}\n"
            f"Tempo total: {tempo:.2f} min (inclui {trocas} troca(s))"
        )
        resultado_texto.delete('1.0', tk.END)
        resultado_texto.insert(tk.END, resultado)
        desenhar_grafo_com_caminho(caminho)
    except Exception as e:
        messagebox.showerror('Erro', str(e))

# ----- Configuração da Interface Tkinter -----
root = tk.Tk()
root.title('Simulador de Metrô')
root.state('zoomed')

# Top frame: inputs dinâmicos
top = ttk.Frame(root)
top.pack(fill='x', padx=10, pady=5)

ttk.Label(top, text=f"Origem (1-{N}):").grid(row=0, column=0)
origem_var = ttk.Entry(top, width=5); origem_var.grid(row=0, column=1)

ttk.Label(top, text=f"Destino (1-{N}):").grid(row=0, column=2)
destino_var = ttk.Entry(top, width=5); destino_var.grid(row=0, column=3)

ttk.Label(top, text="Penalidade troca (min):").grid(row=0, column=4)
troca_var = ttk.Entry(top, width=5); troca_var.insert(0, '0'); troca_var.grid(row=0, column=5)

ttk.Button(top, text='Calcular', command=calcular).grid(row=0, column=6, padx=10)

# Área de texto para resultado
resultado_texto = tk.Text(root, height=3, font=('Consolas', 11))
resultado_texto.pack(fill='x', padx=10, pady=5)

# Frame para o gráfico
fig_frame = ttk.Frame(root)
fig_frame.pack(expand=True, fill='both')

# Cria figura Matplotlib fora da função para reuso
g_fig, ax = plt.subplots(figsize=(8, 6))
fig = g_fig

# Loop principal
root.mainloop()
