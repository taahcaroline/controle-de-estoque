
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .forms import CadastroitensForm, CadastroprodutoForm
from .models import Cadastroitens, Produto
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils.timezone import now
from datetime import timedelta
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Sum


from django.template.loader import render_to_string
from fpdf import FPDF
from .models import Movimentacao, MovimentacaoItem


# Create your views here.
def home(request):
    return render(request, 'index.html')





    
def cadastro(request):
    if request.method == 'POST':
        form = CadastroitensForm(request.POST)
        if form.is_valid():
            form.save()  # Salva o novo item no banco de dados
            messages.success(request, 'Produto cadastrado com sucesso!')
            return redirect('cadastro')
    else:
        form = CadastroitensForm()

    return render(request, 'cadastromateriais.html', {'form': form})    

    
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



# ------------------ Baixa de estoque múltipla ------------------
# def baixa_estoque(request):
#     produtos = Produto.objects.all()  # Carrega todos os produtos

#     if request.method == 'POST':
#         tipo_mov = request.POST.get('tipo_movimentacao')
#         requisitante = request.POST.get('requisitante')

#         # Pegando listas de itens
#         produto_ids = request.POST.getlist('produto_id[]')
#         lote_ids = request.POST.getlist('lote_id[]')
#         quantidades = request.POST.getlist('quantidade_baixada[]')

#         for produto_id, lote_id, qtd in zip(produto_ids, lote_ids, quantidades):
#             try:
#                 quantidade_baixada = int(qtd)
#             except ValueError:
#                 messages.error(request, 'Quantidade inválida.')
#                 continue

#             try:
#                 item = Cadastroitens.objects.get(id=lote_id, produto_id=produto_id)
#             except Cadastroitens.DoesNotExist:
#                 messages.error(request, f'Lote ou produto não encontrado (produto {produto_id}).')
#                 continue

#             if quantidade_baixada > item.quantidade:
#                 messages.error(request, f'Quantidade insuficiente no lote {item.lote}.')
#             else:
#                 item.quantidade -= quantidade_baixada
#                 item.save()
#                 messages.success(
#                     request,
#                     f"{quantidade_baixada} unidades de '{item.produto.nome}' (lote {item.lote}) baixadas com sucesso. "
#                     f"Tipo: {tipo_mov}, Requisitante: {requisitante}"
#                 )

#         return redirect('baixa')  # Só retorna depois de processar o POST

#     # Apenas GET ou outros métodos
#     return render(request, 'baixa.html', {'produtos': produtos})

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
                quantidade_baixada=quantidade_baixada
            )

        messages.success(request, "Movimentação registrada com sucesso.")
       

    return render(request, 'baixa.html', {'produtos': produtos})

# ------------------ Retorna lotes via AJAX ------------------
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


def excluir_item(request, item_id):
    item = get_object_or_404(Cadastroitens, id=item_id)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Item excluído com sucesso!")
        return redirect('estoque')
    return render(request, 'deletar.html', {'item': item})





from django.http import HttpResponse
from fpdf import FPDF

def gerar_relatorio_pdf(request, movimentacao_id):
    movimentacao = Movimentacao.objects.get(id=movimentacao_id)
    itens = movimentacao.itens.all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Relatório de Baixa de Estoque", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Tipo: {movimentacao.get_tipo_movimentacao_display()}", ln=True)
    pdf.cell(0, 10, f"Requisitante: {movimentacao.requisitante}", ln=True)
    pdf.cell(0, 10, f"Data: {movimentacao.data.strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Produto", border=1)
    pdf.cell(30, 10, "Lote", border=1)
    pdf.cell(30, 10, "Validade", border=1)
    pdf.cell(30, 10, "Fabricante", border=1)
    pdf.cell(30, 10, "Quantidade", border=1)
    pdf.ln()

    pdf.set_font("Arial", size=10)
    for item in itens:
        pdf.cell(40, 10, item.produto.nome, border=1)
        pdf.cell(30, 10, item.lote.lote, border=1)
        pdf.cell(30, 10, item.lote.validade.strftime('%d/%m/%Y'), border=1)
        pdf.cell(30, 10, item.lote.fornecedor, border=1)
        pdf.cell(30, 10, str(item.quantidade_baixada), border=1)
        pdf.ln()

    # Gera o conteúdo do PDF em memória
    pdf_output = pdf.output(dest='S').encode('latin1')

    response = HttpResponse(pdf_output, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="baixa_estoque.pdf"'
    return response

from django.shortcuts import render
from .models import Movimentacao

def historico_movimentacoes(request):
    movimentacoes = Movimentacao.objects.all().order_by('-data')  # mais recentes primeiro

    return render(request, 'historico_movimentacoes.html', {
        'movimentacoes': movimentacoes
    })






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
