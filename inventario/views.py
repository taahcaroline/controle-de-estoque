
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import CadastroitensForm, CadastroprodutoForm, CustomLoginForm, RegistroUsuarioForm
from .models import Cadastroitens, Produto, Movimentacao, MovimentacaoItem
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
from django.utils.timezone import now
from datetime import timedelta, datetime
from django.template.loader import render_to_string
from fpdf import FPDF
from django.contrib.auth import authenticate, login, logout
from io import BytesIO

def registrar(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('login')  
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
           
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                # messages.success(request, f'Bem-vindo, {user.username}!')
                return redirect('home') 
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
        else:
            messages.error(request, 'Há erros no formulário. Corrija e tente novamente.')
    else:
        form = CustomLoginForm()

    return render(request, 'registration/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Você saiu da sua conta com sucesso.')
    return redirect('login') 


def home(request):
    return render(request, 'index.html')




@login_required
def cadastro(request):
    if request.method == 'POST':
        origem = request.POST.get('origem')
        produtos = request.POST.getlist('produto')
        lotes = request.POST.getlist('lote')
        validades = request.POST.getlist('validade')
        quantidades = request.POST.getlist('quantidade')
        unidades = request.POST.getlist('unidade')
        fornecedores = request.POST.getlist('fornecedor')

        total_itens = len(produtos)

        for i in range(total_itens):
            data = {
                'origem': origem,
                'produto': produtos[i],
                'lote': lotes[i],
                'validade': validades[i],
                'quantidade': quantidades[i],
                'unidade': unidades[i],
                'fornecedor': fornecedores[i],
            }

            form = CadastroitensForm(data)

            if form.is_valid():
                produto = form.cleaned_data['produto']
                lote = form.cleaned_data['lote']
                validade = form.cleaned_data['validade']

                item_existente = Cadastroitens.objects.filter(
                    produto=produto,
                    lote=lote,
                    validade=validade
                ).first()

                if item_existente:
                    item_existente.quantidade += form.cleaned_data['quantidade']
                    item_existente.unidade = form.cleaned_data['unidade']
                    item_existente.fornecedor = form.cleaned_data['fornecedor']
                    item_existente.origem = form.cleaned_data['origem']
                    item_existente.save()

                    messages.success(request, f'Estoque atualizado para o produto "{produto}".')
                else:
                    form.save()
                    messages.success(request, f'Produto "{produto}" cadastrado com sucesso!')
            else:
                errors = form.errors.as_text()
                messages.error(request, f'Erro ao cadastrar item {i+1}: {errors}')

        return redirect('cadastro')

    else:
        form = CadastroitensForm()

    return render(request, 'cadastromateriais.html', {'form': form})
  

@login_required    
def cadastroproduto(request):
    if request.method == 'POST':
        form = CadastroprodutoForm(request.POST)
        if form.is_valid():
            form.save()  # Salva o novo item no banco de dados
            messages.success(request, 'Produto cadastrado com sucesso!')
            return redirect('cadastroproduto')
    else:
        form = CadastroprodutoForm()

    return render(request, 'cadastroproduto.html', {'form': form})    


@login_required
def baixa_estoque(request):
    produtos = Produto.objects.all()

    if request.method == 'POST':
        tipo_mov = request.POST.get('tipo_movimentacao')
        requisitante = request.POST.get('requisitante')
        produto_ids = request.POST.getlist('produto_id[]')
        lote_ids = request.POST.getlist('lote_id[]')
        quantidades = request.POST.getlist('quantidade_baixada[]')

        movimentacao = Movimentacao.objects.create(
            tipo_movimentacao=tipo_mov,
            requisitante=requisitante
        )

        for produto_id, lote_id, qtd in zip(produto_ids, lote_ids, quantidades):
            item = Cadastroitens.objects.get(id=lote_id)
            quantidade_baixada = int(qtd)

            if quantidade_baixada > item.quantidade:
                messages.error(request, f"Quantidade insuficiente no lote {item.lote}.")
                continue

            item.quantidade -= quantidade_baixada
            item.save()

            MovimentacaoItem.objects.create(
                movimentacao=movimentacao,
                produto=item.produto,
                lote=item,
                quantidade_baixada=quantidade_baixada,
                descricao=item.produto,
            )

        messages.success(request, "Movimentação registrada com sucesso.")
       

    return render(request, 'baixa.html', {'produtos': produtos})

@login_required
def get_lotes(request, produto_id):
    lotes = Cadastroitens.objects.filter(produto_id=produto_id).select_related('produto').values(
        'id', 'lote', 'validade', 'fornecedor', 'produto__descricao'
    )

    lotes_data = []
    for lote in lotes:
        lotes_data.append({
            'id': lote['id'],
            'lote': lote['lote'],
            'descricao': lote['produto__descricao'] or "",  # protege contra None
            'validade': lote['validade'].strftime('%d/%m/%Y'),
            'fornecedor': lote['fornecedor']
        })
    return JsonResponse({'lotes': lotes_data})

@login_required
def estoque(request):
    busca = request.GET.get('q')
    filtro = request.GET.get('filtro')
    hoje = now().date()
    prazo_curto = hoje + timedelta(days=30)
    itens = Cadastroitens.objects.select_related('produto').all().order_by('produto__nome', 'validade')
    if busca:
        if busca:
         itens = itens.filter(
            Q(produto__nome__icontains=busca) |
            Q(fornecedor__icontains=busca) |
            Q(lote__icontains=busca)
        )
    if filtro == "vencidos":
        itens = itens.filter(validade__lt=hoje)
    elif filtro == "validade_proxima":
        itens = itens.filter(validade__range=[hoje, prazo_curto])
    elif filtro == "estoque_baixo":
        itens = itens.filter(quantidade__lt=10)
    elif filtro == "disponivel":
        itens = itens.filter(quantidade__gt=0, validade__gte=hoje)     

    return render(request, 'estoque.html', {'itens': itens,  'busca': busca,
        'filtro': filtro,
        'today': hoje, })

@login_required
def editar_estoque(request, item_id):
    item = get_object_or_404(Cadastroitens, id=item_id)
    if request.method == "POST":
        form = CadastroitensForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item atualizado com sucesso!")
            return redirect('estoque')
    else:
        form = CadastroitensForm(instance=item)
    return render(request, 'editar_estoque.html', {'form': form, 'item': item})

@login_required
def excluir_item(request, item_id):
    item = get_object_or_404(Cadastroitens, id=item_id)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Item excluído com sucesso!")
        return redirect('estoque')
    return render(request, 'deletar.html', {'item': item})



@login_required
def gerar_relatorio_pdf(request, movimentacao_id):
    movimentacao = Movimentacao.objects.get(id=movimentacao_id)
    itens = movimentacao.itens.all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # -------------------------
    # Título
    # -------------------------
    pdf.cell(0, 10, "Relatório de Saída", ln=True, align="C")
    pdf.ln(10)

    # -------------------------
    # Informações da movimentação
    # -------------------------
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Tipo: {movimentacao.get_tipo_movimentacao_display()}", ln=True)
    pdf.cell(0, 10, f"Requisitante: {movimentacao.requisitante or 'N/A'}", ln=True)
    pdf.cell(0, 10, f"Data: {movimentacao.data.strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)

    # -------------------------
    # Definição de colunas
    # -------------------------
    columns = [
        {"title": "Produto", "width": 60},
        {"title": "Lote", "width": 25},
        {"title": "Validade", "width": 25},
        {"title": "Fornecedor", "width": 30},
        {"title": "Quantidade", "width": 25},
        {"title": "Descrição", "width": 30},
    ]

    # Cabeçalho
    pdf.set_font("Arial", 'B', 10)
    for col in columns:
        pdf.cell(col["width"], 10, col["title"], border=1, align='C')
    pdf.ln()

    # -------------------------
    # Função para calcular número de linhas de um texto
    # -------------------------
    def calc_lines(text, col_width, line_height):
        """Calcula o número de linhas necessárias para um texto, considerando a largura da coluna"""
        # Aproximação simples: largura do texto / largura da coluna
        return max(1, int(pdf.get_string_width(text) / col_width) + 1)

    # -------------------------
    # Conteúdo
    # -------------------------
    pdf.set_font("Arial", size=10)
    for item in itens:
        nome_produto = str(item.produto.nome or 'N/A')
        lote_codigo = str(item.lote.lote or 'N/A')
        validade = item.lote.validade.strftime('%d/%m/%Y') if item.lote.validade else 'N/A'
        fornecedor = str(item.lote.fornecedor or 'N/A')
        quantidade = str(item.quantidade_baixada or 0)
        descricao_item = item.produto.descricao or 'N/A'

        # Altura de cada linha do nome_produto reduzida
        line_height = 6  # menor que 10 para aproximar linhas quebradas

        # Calcula número de linhas necessárias para o nome_produto
        lines_produto = calc_lines(nome_produto, 60, line_height)
        total_height = line_height * lines_produto

        # Salva posição inicial
        x_start = pdf.get_x()
        y_start = pdf.get_y()

        # Produto com quebra de linha e espaçamento menor
        pdf.multi_cell(60, line_height, nome_produto, border=1)
        pdf.set_xy(x_start + 60, y_start)

        # Outras células seguem a mesma altura total
        pdf.cell(25, total_height, lote_codigo, border=1)
        pdf.cell(25, total_height, validade, border=1)
        pdf.cell(30, total_height, fornecedor, border=1)
        pdf.cell(25, total_height, quantidade, border=1)

        # Descrição sem quebra de linha
        pdf.cell(30, total_height, descricao_item, border=1)

        # Ajusta posição para a próxima linha
        pdf.set_xy(x_start, y_start + total_height)

    # -------------------------
    # Gera PDF
    # -------------------------
    pdf_output = pdf.output(dest='S').encode('latin1')
    response = HttpResponse(pdf_output, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="baixa_estoque.pdf"'
    return response

@login_required
def historico_movimentacoes(request):
    movimentacoes = Movimentacao.objects.all().order_by('-data')  # mais recentes primeiro

    return render(request, 'historico_movimentacoes.html', {
        'movimentacoes': movimentacoes
    })


@login_required
def relatorio_consumo_periodo(request):
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    produtos = Produto.objects.all()

    if data_inicio and data_fim:
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d')
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d')
        except ValueError:
            return render(request, 'relatorio_periodo.html', {
                'erro': 'Formato de data inválido.',
                'produtos': produtos
            })

        # Filtrar e agrupar
        itens_agrupados = (
            MovimentacaoItem.objects
            .filter(
                movimentacao__data__date__gte=dt_inicio.date(),
                movimentacao__data__date__lte=dt_fim.date()
            )
            .values('produto__nome')  # Agrupar por nome do produto
            .annotate(total=Sum('quantidade_baixada'))
            .order_by('produto__nome')
        )

        # Gerar o PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        titulo = f"Relatório de Consumo Consolidado\nPeríodo: {data_inicio} a {data_fim}"
        pdf.multi_cell(0, 10, titulo, align='C')
        pdf.ln(5)

        # Cabeçalho
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(130, 10, "Produto", border=1)
        pdf.cell(50, 10, "Total Consumido", border=1)
        pdf.ln()

        pdf.set_font("Arial", size=10)

        if not itens_agrupados:
            pdf.cell(0, 10, "Nenhum consumo registrado no período.", ln=True)
        else:
            for item in itens_agrupados:
                pdf.cell(130, 10, item['produto__nome'][:40], border=1)
                pdf.cell(50, 10, str(item['total']), border=1)
                pdf.ln()

        # Gerar PDF para resposta
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="relatorio_consolidado_{data_inicio}_a_{data_fim}.pdf"'
        return response

    # Página inicial (sem GET)
    return render(request, 'relatorio_periodo.html', {
        'produtos': produtos
    })
@login_required
def gerar_relatorio_entrada_pdf(request, cadastroitens_id):
    lote = Cadastroitens.objects.get(id=cadastroitens_id)

    # Gera o PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Relatório de Entrada", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Data de Entrada: {lote.data.strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(0, 10, f"Origem: {lote.get_origem_display()}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Produto", border=1)
    pdf.cell(30, 10, "Lote", border=1)
    pdf.cell(20, 10, "Validade", border=1)
    pdf.cell(40, 10, "Fornecedor", border=1)
    pdf.cell(30, 10, "Quantidade", border=1)
    pdf.cell(30, 10, "Unidade", border=1)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    pdf.cell(40, 10, lote.produto.nome, border=1)
    pdf.cell(30, 10, lote.lote, border=1)
    pdf.cell(20, 10, lote.validade.strftime('%d/%m/%Y'), border=1)
    pdf.cell(40, 10, lote.fornecedor, border=1)
    pdf.cell(30, 10, str(lote.quantidade), border=1)
    pdf.cell(30, 10, lote.produto.descricao or 'N/A', border=1)
    pdf.ln()

    # Retorna o PDF
    pdf_output = pdf.output(dest='S').encode('latin1')
    response = HttpResponse(pdf_output, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="entrada_estoque.pdf"'
    return response

def historico_entradas(request):
    entradas = Cadastroitens.objects.order_by('-data')
    return render(request, 'historico_entrada.html', {
        'movimentacoes': entradas
    })
    
@login_required    
def relatorio_estoque(request):
    # Obtém todos os produtos do banco de dados
    produtos = Cadastroitens.objects.all()
    
    # Passa os dados para o template
    return render(request, 'relatorio_estoque.html', {'produtos': produtos})

@login_required
def relatorio_estoque_pdf(request):
    # Obtém todos os produtos do banco de dados
    produtos = Cadastroitens.objects.all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Relatório de Estoque", ln=True, align="C")
    pdf.ln(10)

    # Cabeçalhos
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(20, 10, "ID", border=1)
    pdf.cell(40, 10, "Produto", border=1)
    pdf.cell(30, 10, "Descrição", border=1)
    pdf.cell(30, 10, "Lote", border=1)
    pdf.cell(30, 10, "Validade", border=1)
    pdf.cell(30, 10, "Quantidade", border=1)
   
    pdf.ln()
    
   

    # Dados
    pdf.set_font("Arial", size=10)
    for p in produtos:
        pdf.cell(20, 10, str(p.produto.id), border=1)
        pdf.cell(40, 10, str(p.produto.nome)[:20], border=1)
        pdf.cell(30, 10, str(p.produto.descricao)[:30], border=1)
        pdf.cell(30, 10, str(p.lote), border=1)
        pdf.cell(30, 10, str(p.validade), border=1)
        pdf.cell(30, 10, str(p.quantidade), border=1)
        pdf.ln()

    pdf_data = pdf.output(dest='S').encode('latin1')
   

    # Retorna como resposta HTTP
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="relatorio_estoque.pdf"'
    return response
