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



def init_db ():
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
                            selc_diaria REAL
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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: #e2e8f0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            width: 100%;
            max-width: 600px;
            background: rgba(15, 23, 42, 0.95);
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-weight: 600;
            letter-spacing: 1px;
            color: #f1f5f9;
        }

        form {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        label {
            font-size: 14px;
            color: #94a3b8;
            margin-bottom: 5px;
        }

        input[type="file"] {
            padding: 10px;
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 6px;
            color: #cbd5e1;
            cursor: pointer;
        }

        input[type="file"]::file-selector-button {
            background-color: #334155;
            color: #e2e8f0;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            transition: 0.3s ease;
        }

        input[type="file"]::file-selector-button:hover {
            background-color: #475569;
        }

        input[type="submit"] {
            margin-top: 10px;
            padding: 12px;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            border: none;
            border-radius: 6px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: 0.3s ease;
        }

        input[type="submit"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.4);
        }

        .links {
            margin-top: 30px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .links a {
            text-decoration: none;
            color: #cbd5e1;
            padding: 10px;
            background-color: #1e293b;
            border-radius: 6px;
            text-align: center;
            transition: 0.3s ease;
            border: 1px solid #334155;
        }

        .links a:hover {
            background-color: #334155;
            color: #ffffff;
            transform: translateX(5px);
        }

        hr {
            margin-top: 30px;
            border: none;
            height: 1px;
            background-color: #334155;
        }

        @media (max-width: 600px) {
            .container {
                padding: 25px;
            }
        }
    </style>
</head>

<body>
    <div class="container">
        <h1>Upload de Dados Econômicos</h1>

        <form action="/upload" method="POST" enctype="multipart/form-data">
            
            <div>
                <label for="campo_inadimplencia">Arquivo de Inadimplência</label>
                <input name="campo_inadimplencia" type="file" required>
            </div>

            <div>
                <label for="campo_selic">Arquivo de Taxa Selic</label>
                <input name="campo_selic" type="file" required>
            </div>

            <input type="submit" value="Fazer Upload">
        </form>

        <div class="links">
            <a href="/consultar">Consultar Dados Armazenados</a>
            <a href="/graficos">Ver Gráficos</a>
            <a href="/editar_inadimplencia">Editar Dados de Inadimplência</a>
            <a href="/editar_selic">Editar Dados de SELIC</a>
            <a href="/correlacao">Analisar Correlação</a>
        </div>

        <hr>
    </div>
</body>
</html>
''')

@app.route('/upload', methods = ['POST', 'GET'])
def upload():
    inad_file = request.files.get('campo_inadimplencia')
    selic_file = request.files.get('campo_selic')

    if not inad_file or not selic_file:
        return jsonify({'Erro': 'Ambos os dados devem ser enviados'})

    inad_df = pd.read_csv(
        inad_file,
        sep = ';',
        names = ['data', 'inadimplencia'],
        header = 0
    )
    selic_df = pd.read_csv(
        selic_file,
        sep = ';',
        names = ['data', 'selic_diaria'],
        header = 0
    )

    inad_df['data'] = pd.to_datetime(inad_df['data'], format = '%d/%m/%Y')
    selic_df['data'] = pd.to_datetime(selic_df['data'], format = '%d/%m/%Y')
    
    inad_df['mes'] =  inad_df['data'].dt.to_period('M').astype(str)
    selic_df['mes'] =  selic_df['data'].dt.to_period('M').astype(str)

    inad_mensal = inad_df[['mes', 'inadimplencia']].drop_duplicates()
    selic_mensal = selic_df.groupby('mes')['selic_diaria'].mean().reset_index()


    with sqlite3.connect(DB_PATH) as conn:
        inad_mensal.to_sql('inadimplencia', conn, if_exists = 'replace', index = False)
        selic_mensal.to_sql('selic', conn, if_exists = 'replace', index = False)
    return jsonify({'Mensagem':'Dados armazenados com sucesso.'})

@app.route('/consultar', methods=['POST', 'GET'])
def consultar():
    if request.method == 'POST':
        tabela = request.form.get('campo_tabela')
        
        if tabela not in ['inadimplencia', 'selic']:
            return jsonify({'Erro', 'Tabela inválida'}) 
        
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
        return df.to_html(index=False)
        

    return render_template_string('''
        <h1> Consultar de Tabelas </h1>
        <form method='POST' action='/consultar'>
            <label> Escolha a tabela:</label>
            <select name = 'campo_tabela'>
                 <option value = 'inadimplencia'> Inadimplência </option>
                 <option value = 'selic'> Tava Selic </option>                                  
            </select>
            <input type='submit' value= 'Consultar'>
        </form>
        <br>
        <a href='/'> Voltar </a>

''')

@app.route('/editar_inadimplencia', methods = ['POST', 'GET'])
def editar_inadimplencia():
    if request.method == 'POST':
            mes = request.form.get('campo_mes')
            novo_valor = request.form.get('campo_valor')

            try:
                novo_valor = float(novo_valor)
            except:
                return jsonify({'Erro':'Valor Invalido'})
            
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE inadimplencia SET inadimplencia = ? WHERE mes = ?', (novo_valor, mes))
                conn.commit()
            return jsonify({'Mensagem':f'Valor atualizado com sucesso para o de {mes}'})   

    return render_template_string('''
        <h1> Editar Inadimplencia </h1>
        <form method = 'POST' action = '/editar_inadimplencia'>    
            <label for='campo_mes'> Mês(AAAA-MM): </label>
            <input type='text' name='campo_mes'> <br>     

            <label for='campo_valor'> Novo Valor de Inadimplência: </label>
            <input type='text' name='campo_valor'> <br>  

            <input type='submit' value=' Atualizar dados '>
            <br>
            <a href='/'> Voltar </a>                                                                                             
        </from>
 ''')

@app.route('/editar_selic', methods = ['POST', 'GET'])
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
                cursor.execute('UPDATE selic SET selic_diaria = ? WHERE mes = ?', (novo_valor, mes))
                conn.commit()
            return jsonify({'Mensagem':f'Valor atualizado com sucesso para o de {mes}'})   

    return render_template_string('''
        <h1> Editar SELIC </h1>
        <form method = 'POST' action = '/editar_selic'>    
            <label for='campo_mes'> Mês(AAAA-MM): </label>
            <input type='text' name='campo_mes'> <br>     

            <label for='campo_valor'> Novo Valor de SELIC: </label>
            <input type='text' name='campo_valor'> <br>  

            <input type='submit' value=' Atualizar dados '>
            <br>
            <a href='/'> Voltar </a>                                                                                             
        </from>
 ''')

@app.route('/graficos')
def grafico():
    with  sqlite3.connect(DB_PATH) as conn:
        inad_df = pd.read_sql_query('SELECT * FROM inadimplencia', conn)
        selic_df = pd.read_sql_query('SELECT * FROM selic', conn)
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
            x = inad_df['mes'],
            y = inad_df['inadimplencia'],
            mode = 'lines+markers',
            name = 'Inadimplencia'
        )
    )

    fig1.update_layout(
        title = 'Evolução da Inadimplencia',
        xaxis_title = 'Mês',
        yaxis_title = '%',
        template ='plotly_dark'
    )

    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
            x = selic_df['mes'],
            y = selic_df['selic_diaria'],
            mode = 'lines+markers',
            name = 'Selic'
        )
    )

    fig2.update_layout(
        title = 'Evolução da Selic',
        xaxis_title = 'Mês',
        yaxis_title = 'SELIC',
        template ='plotly_dark'
    )
    
    grafico_hmtl1 = fig1.to_html(full_html=False, include_plotlyjs = 'cdn')
    grafico_hmtl2 = fig2.to_html(full_html=False, include_plotlyjs = False)

    return render_template_string('''                       
        <html>
            <head>
                <title> Graficos Economicos </title>
                <style>
                    body{background-color:black;}
                    .container{
                        display:flex;
                        justify-content:space-around
                    }

                    .graph{
                        width:48%;          
                                  }
                </style>
            </head>
            <body>
                <h1> Graficos Economicos </h1>
                <div class = "container">
                    <div class = "graph">  {{ grafico1|safe }} </div>
                    <div class = "graph"> {{ grafico2|safe }} </div>
                </div>
            </body>                               
        </html>
                                  
    ''',grafico1 = grafico_hmtl1, grafico2 = grafico_hmtl2)


@app.route('/correlacao')
def correlacao():


    with  sqlite3.connect(DB_PATH) as conn:
        inad_df = pd.read_sql_query('SELECT * FROM inadimplencia', conn)
        selic_df = pd.read_sql_query('SELECT * FROM selic', conn)

    #consilidação das tabelas 

    merged = pd.merge(inad_df, selic_df, on='mes')

    '''
    O restultado da correlação de pearson  é: 

    1:: quando a selic, sobe inadimplencia sobe perfeitamente (corelação positiva)
    0:: não existe correlação
    -1:: quando selic sobe, inadimplencia cai perfeitamente (correlação negativa) 
    '''
    correl = merged['inadimplencia'].corr(merged['selic_diaria'])

    #Regressão linear para visualização

    x = merged['selic_diaria']
    y = merged['inadimplencia']

    '''
    O polyfit retorna um array de polinomios, onde o grau 1 devolve dois valores
    [m] sera nosso coefienciente angula (inclinação da reta)
    [b] sera nosso coefienciente linear (intercepto(valor y quando x = 0))
    
    '''

    m, b = np.polyfit(x, y, 1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
            x = x,
            y = y, 
            mode = 'markers', 
            name = "Inadimplência X SELIC",
            hovertemplate = 'SELIC: %{x:.2f}%<br>Inadimplência: %{x:.2f}% <extra></extra>', 
            marker = dict(
                    color = 'rgba(0, 123, 255,0.8)',
                    size = 12,
                    line = dict(
                            width = 2,
                            color = 'white'
                        ),
                    symbol = 'circle'
                )
        )
    )

    # Grafico da linha de tendencia 
    fig.add_trace(go.Scatter(        
            x = x,
            y = m * x + b,
            mode = 'lines',
            name = 'Linha de Tendencia',
            line = dict(
                    color = 'rgba(220, 53, 69, 1)',
                    width = 4,
                    dash = 'dot' #definição de linha pontilhada
             )
        )
    )

    fig.update_layout(
        title = {
            'text':'<b>Correlação entre SELIC e Indimplência</b><br><span style="font-size:16px:">Coeficiente de Correlação {correl:.2f}</span>',
            'y':0.95,
            'x':0.5,
            'xanchor':'center',
            'yanchor':'top',
        },
        xaxis_title = dict(
            text = 'Selic Média Mensal (%)',
            font = dict(size=18, family = 'Arial', color = 'gray')
        ),
        yaxis_title = dict(
            text = 'Inadimplência (%)',
            font = dict(size=18, family = 'Arial', color = 'gray')
        ),
        xaxis = dict(
            tickfont = dict(size = 14, family = 'Arial', color = 'black'),
            gridcolor = 'lightgray'
        ),
        yaxis = dict(
            tickfont = dict(size = 14, family = 'Arial', color = 'black'),
            gridcolor = 'lightgray'
        ),
        plot_bgcolor = '#f8f9fa',
        paper_bgcolor = 'white',
        font = dict(size = 14, family = 'Arial', color = 'black'),
        legend = dict(
            orientantion = 'h',
            yanchor = 'bottom',
            xanchor = 'center',
            x = 0.5,
            y = 1.05,
            bgcolor = 'rgba(0,0,0,0)',
            borderwidth = 0 
        ),
        margin = dict(l = 60, r = 60, t = 120, b = 60)

    )

    graph_html = fig.to_html(full_html=False, include_plotlyjs='cnd')

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
                <div class = "container">
                    <h1> Correlação Selic vs Inadimplência </h1>
                    <div> {{ grafico_carelacao|safe }} </div>
                    <br>
                    <div> <a href='/'> </a> </div>
                </div>
            </body>                           
        </html>
''', grafico_carelacao = graph_html)


if __name__ == '__main__':


    init_db()
    app.run(debug=True)


