
from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import sqlite3
import os
import config
import plotly.graph_objs as go
import dash
from dash import Dash, html, dcc
import numpy as np

app = Flask(__name__)
DB_PATH = config.DB_PATH

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS inadimplencia(
                            mes TEXT PRIMARY KEY,
                            inadimplencia REAL
                       )
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS selic(
                            mes TEXT PRIMARY KEY,
                            selic_diaria REAL
                       )
                       ''')
        conn.commit()
@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Upload de Dados Econômicos</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            --card-bg: #ffffff;
            --primary: #1f4fd8;
            --secondary: #4b5563;
            --accent: #10b981;
            --border: #e5e7eb;
            --text-dark: #111827;
            --text-light: #6b7280;
            --shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
            --radius: 14px;
        }

        * {
            box-sizing: border-box;
            font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        body {
            margin: 0;
            min-height: 100vh;
            background: var(--bg-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px 16px;
        }

        .container {
            background: var(--card-bg);
            width: 100%;
            max-width: 520px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 40px;
            animation: fadeIn 0.6s ease-out;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        h1 {
            margin-top: 0;
            margin-bottom: 32px;
            font-size: 26px;
            color: var(--text-dark);
            text-align: center;
            letter-spacing: 0.4px;
        }

        form {
            display: flex;
            flex-direction: column;
            gap: 22px;
        }

        label {
            font-size: 14px;
            font-weight: 600;
            color: var(--secondary);
            margin-bottom: 6px;
        }

        .file-group {
            display: flex;
            flex-direction: column;
        }

        input[type="file"] {
            padding: 10px;
            border: 2px dashed var(--border);
            border-radius: 10px;
            background-color: #f9fafb;
            cursor: pointer;
            transition: border-color 0.3s, background-color 0.3s;
        }

        input[type="file"]:hover {
            border-color: var(--primary);
            background-color: #f0f5ff;
        }

        input[type="submit"] {
            margin-top: 10px;
            padding: 14px;
            font-size: 15px;
            font-weight: 600;
            color: #ffffff;
            background: linear-gradient(135deg, var(--primary), #3b82f6);
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s, opacity 0.2s;
            box-shadow: 0 10px 20px rgba(31, 79, 216, 0.25);
        }

        input[type="submit"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 14px 28px rgba(31, 79, 216, 0.35);
            opacity: 0.95;
        }

        .links {
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid var(--border);
            display: grid;
            gap: 14px;
        }

        .links a {
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            color: var(--primary);
            padding: 10px 14px;
            border-radius: 8px;
            transition: background-color 0.25s, color 0.25s;
        }

        .links a:hover {
            background-color: #eef2ff;
            color: #1e40af;
        }

        footer {
            margin-top: 28px;
            text-align: center;
            font-size: 12px;
            color: var(--text-light);
        }

        @media (max-width: 480px) {
            .container {
                padding: 28px 22px;
            }

            h1 {
                font-size: 22px;
            }
        }
    </style>
</head>

<body>
    <div class="container">
        <h1>Upload de Dados Econômicos</h1>

        <form action="/upload" method="POST" enctype="multipart/form-data">
            <div class="file-group">
                <label for="campo_inadimplencia">Arquivo de Inadimplência (CSV)</label>
                <input id="campo_inadimplencia" name="campo_inadimplencia" type="file" accept=".csv">
            </div>

            <div class="file-group">
                <label for="campo_selic">Arquivo de Taxa Selic (CSV)</label>
                <input id="campo_selic" name="campo_selic" type="file" accept=".csv">
            </div>

            <input type="submit" value="Fazer Upload">
        </form>

        <div class="links">
            <a href="/consultar">Consultar dados armazenados</a>
            <a href="/graficos">Ver gráficos</a>
            <a href="/editar_inadimplencia">Editar dados de inadimplência</a>
            <a href="/editar_selic">Editar dados da taxa Selic</a>
            <a href="/correlacao">Analisar correlação</a>
        </div>

        <footer>
            Sistema de Análise Econômica • Interface Profissional
        </footer>
    </div>
</body>
</html>
    ''')

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    inad_file = request.files.get('campo_inadimplencia')
    selic_file = request.files.get('campo_selic')

    if not inad_file or not selic_file:
        return jsonify({"Erro":"Ambos os dados devem ser enviados"})

    inad_df = pd.read_csv(
        inad_file,
        sep = ";",
        names = ['data','inadimplencia'],
        header = 0
    )
    selic_df = pd.read_csv(
        selic_file,
        sep = ";",
        names = ['data','selic_diaria'],
        header = 0
    )

    inad_df['data'] = pd.to_datetime(inad_df['data'], format='%d/%m/%Y')
    selic_df['data'] = pd.to_datetime(selic_df['data'], format='%d/%m/%Y')

    inad_df['mes'] = inad_df['data'].dt.to_period('M').astype(str)
    selic_df['mes'] = selic_df['data'].dt.to_period('M').astype(str)

    inad_mensal = inad_df[['mes','inadimplencia']].drop_duplicates()
    selic_mensal = selic_df.groupby('mes')['selic_diaria'].mean().reset_index()

    with sqlite3.connect(DB_PATH) as conn:
        inad_mensal.to_sql('inadimplencia', conn, if_exists='replace', index=False)
        selic_mensal.to_sql('selic', conn, if_exists='replace', index=False)
    return jsonify({'Mensagem':'Dados armazenados com sucesso.'})
'''
    Alternativa para nao usar o with
    conn = sqlite3.connect(DB_PATH)
    try:
        inad_mensal.to_sql('inadimplencia', conn, if_exists='replace', index='False')
        selic_mensal.to_sql('selic', conn, if_exists='replace', index='False')
    finally:
        conn.close()
'''
@app.route('/consultar', methods=['POST','GET'])
def consultar():
    if request.method == "POST":
        tabela = request.form.get('campo_tabela')

        if tabela not in ['inadimplencia','selic']:
            return jsonify({'Erro':'Tabela inválida'})

        with sqlite3.connect(DB_PATH) as conn: 
            df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
        return df.to_html(index=False)

    return render_template_string('''
        <h1> Consulta de Tabelas </h1>
        <form method="POST" action="/consultar">
            <label> Escolha a tabela: </label>
            <select name="campo_tabela">
                <option value="inadimplencia"> Inadimplência </option>
                <option value="selic"> Taxa Selic </option>
            </select>
            <input type="submit" value=" Consultar ">
        </form>
        <br>
        <a href="/"> Voltar </a>              
    ''')

@app.route('/editar_inadimplencia', methods=['POST','GET'])
def editar_inadimplencia():
        if request.method == "POST":
            mes = request.form.get('campo_mes')
            novo_valor = request.form.get('campo_valor')
            try:
                novo_valor = float(novo_valor)
            except:
                return jsonify({'Erro':'Valor Invalido'})
            
            with sqlite3.connect(DB_PATH) as conn: 
                cursor = conn.cursor()
                cursor.execute("UPDATE inadimplencia SET inadimplencia = ? WHERE mes = ?", (novo_valor,mes))
                conn.commit()
            return jsonify({'Mensagem':f'Valor atualizado com successo para {mes}'})

        return render_template_string('''
            <h1> Editar Inadimplencia </h1>
            <form method="POST" action="/editar_inadimplencia">
                <label for="campo_mes"> Mês (AAAA-MM): </label>
                <input type="text"  name="campo_mes"><br>
                                      
                <label for="campo_valor"> Novo valor de Inadimplência: </label>
                <input type="text" name="campo_valor"><br>
                                      
                <input type="submit" value=" Atualizar dados ">
                <br>
                <a href='/'> Voltar </a>
            </form>
        ''')

@app.route('/editar_selic', methods=['POST','GET'])
def editar_selic():
    if request.method == 'POST':
        mes = request.form.get('campo_mes')
        novo_valor = request.form.get('campo_valor')
        try:
            novo_valor = float(novo_valor)
        except:
            return jsonify({'Erro':'Valor Invalido'})
        
        with sqlite3.connect(DB_PATH) as conn: 
            cursor = conn.cursor()
            cursor.execute("UPDATE selic SET selic_diaria = ? WHERE mes = ?", (novo_valor,mes ))
            conn.commit()
        return jsonify({'Mensagem':f'Valor atualizado com successo para {mes}'})  
    
    return render_template_string('''
        <h1> Editar Taxa Selic </h1>
            <form method="POST" action="/editar_selic">
                <label for="campo_mes"> Mês (AAAA-MM): </label>
                <input type="text"  name="campo_mes"><br>
                                      
                <label for="campo_valor"> Novo valor da Selic: </label>
                <input type="text" name="campo_valor"><br>
                                      
                <input type="submit" value=" Atualizar dados ">
                <br>
                <a href='/'> Voltar </a>
            </form>
    ''')

@app.route('/graficos')
def graficos():
    with sqlite3.connect(DB_PATH) as conn:
        inad_df = pd.read_sql_query('SELECT * FROM inadimplencia', conn)
        selic_df = pd.read_sql_query('SELECT * FROM selic', conn)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x = inad_df['mes'],
        y = inad_df['inadimplencia'],
        mode = 'lines+markers',
        name = 'inadimplencia'
        )
    )
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x = selic_df['mes'],
        y = selic_df['selic_diaria'],
        mode = 'lines+markers',
        name = 'Taxa_selic'
        )
    )
    # ggplot2, seaborn, simple_white, ploty, ploty_white, ploty_dark, xgridoff, ygridoff, gridon, none#
    fig1.update_layout(
        title = 'Evolução da inadimplência',
        xaxis_title = 'Mês',
        yaxis_title = '%',
        template = 'plotly_dark'
    )
    fig2.update_layout(
        title = 'Evolução taxa Selic',
        xaxis_title = 'Mês',
        yaxis_title = '%',
        template = 'plotly_dark'
    )

    grafico_html1 = fig1.to_html(full_html=False, include_plotlyjs='cdn')
    grafico_html2 = fig2.to_html(full_html=False, include_plotlyjs='cdn')
    
    return render_template_string('''
        <html>
            <head>
                <title> Graficos Economicos </title>
                <style> 
                    .container{
                        display: flex;
                        justify-content: space-around;
                    
                    }
                    .graph{
                        with:48%;
                    }
                </style>
            </head>
            <body>
                <h1> Graficos Economicos </h1>
                <div class="container">
                    <div class="graph"> {{grafico1|safe}} </div>                                
                    <div> {{grafico2|safe}} </div>
                </div>
            </body>               
        </html>                
    ''', grafico1 = grafico_html1, grafico2 = grafico_html2)

@app.route('/correlacao')
def correlacao():

    with sqlite3.connect(DB_PATH) as conn:
        inad_df = pd.read_sql_query('SELECT * FROM inadimplencia', conn)
        selic_df = pd.read_sql_query('SELECT * FROM selic', conn)

    merged = pd.merge(inad_df,selic_df, on="mes")

    '''
    0 resultado da correl é:
    1 :: quando a selic sobe, inadimplencia sobe perfeitamente (correlação positiva)
    0 :: não existe correlação
    -1 quando a selicsobe, inadimplencia cai perfeitamente (correlação negativa)
    '''

    correl = merged['inadimplencia'].corr(merged['selic_diaria'])

#Regressão Linear para visualização.
    x = merged['selic_diaria']
    y = merged['inadimplencia']

    '''
    O Polyfit retorna um array de polinomios, ode o grau 1 devolve dosi valores
    [m] será nosso coeficiente angular (inclinação da reta)
    [b] sera nosso coeficiente linear (interceptor(valor de y quando x = 0))
    '''

    m, b = np.polyfit(x, y, 1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
            x = x,
            y = y,
            mode = 'markers',
            name = "Inadimplencia x Selic",
            hovertemplate = 'SELIC; %(X:.2f)% <br>Inadimplencia: %(y:.2f)% <extra></extra>',
            marker = dict(
                    color = 'rgba(0, 123, 255, 0.8)',
                    size = 12,
                    line = dict(
                            width = 2,
                            color = 'white'
                    ),
                    symbol = 'circle'
            ) 
        )
    )

    fig.add_trace(go.Scatter(
            x = x,
            y = m * x + b,
            mode = 'lines',
            name = 'Linha de Tendencia',
            line = dict(
                color = 'rgba(212, 10, 19, 1)',
                width = 10, #Define a largura da linha
                dash = 'dot' #Define o tipo da linha 
            )
        )
    )

    fig.update_layout(
        title = {
            'text':'<b>Correlação entre Selic e Inadimplencia</b><br><span style= "font-size:16px;">'Coeficiente de Correlação: {correl:.2f}</span>', 
            'y':'0.95',
            'x':'0.5',
            'xanchor':'center',
            'yanchor':'top' 
        },
        xaxis_title = dict(
            text = 'Selic Médi Mensal (%)',
            font = dict(size = 22, family= 'Arial', color= 'gray')
        ),
        yaxis_title = dict(
            text = 'Inadimplencia (%)',
            font = dict(size = 22, family= 'Arial', color= 'gray')
        ),
        xaxis = dict(
            tickfont = dict(size=14, family='Arial', color= 'green'),
            gridcolor = 'lightgray'

        ),
        yaxis = dict(
            tickfont = dict(size=14, family='Arial', color= 'green'),
            gridcolor = 'lightgray'

        ),
        plot_bgcolor = '#f8f9fb',
        paper_bgcolor = 'white'
        font = dict(dict(size=14, family='Arial', color= 'green'
        ),
        legend = dict(
            orientantion = 'h',
            yanchor = 'bottom',
            xanchor = 'center',
            x = 0.5,
            y = 1.05,
            bgcolor = 'rgba(1, 1, 1, 1)',
            bordewidth = 0
        ),
        margin = dict(l=60, r=60, t=120, b=60)

    )

    graph_html =fig.to_html(full_html=False, include_plotlyjs= 'cdn')
    return render_template_string('''
            <html>
            <head>
                <title><marquee> Correlação Selic vs Inadimplência </marquee></title>
                <style>
                body{font-family: Arial; background-color: #ffffff; color: #333;}
                .container{width:90%; margin auto; text-align:center;}
                h1{margin-top:40px;}
                a{text-decoration:none; color: #007bff;}
                a:hover{text-decoration:underline;}
                </style>              
            </head>
            <body>
                <div class="container">
                <h1> Correlação Selic vs Inadimplência </h1>
                
                <div> </div> {{grafico_correlacao|safe}} <div>
                <br>
                <div> <a href="/"> Voltar </a> </div> 
                                
            </body>               
        <html>                
    ''', grafico_correlacao = graph_html)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)