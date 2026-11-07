
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="E-Shop Brasil",
    page_icon="🛒",
    layout="wide"
)

# CONEXÃO COM O MONGODB
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")


@st.cache_resource
def conectar_banco():
    if not MONGODB_URI:
        raise ValueError(
            "A variável MONGODB_URI não foi encontrada no arquivo .env"
        )

    cliente_mongo = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000
    )

    cliente_mongo.admin.command("ping")
    return cliente_mongo


try:
    cliente_mongo = conectar_banco()
    db = cliente_mongo["e_shop_brasil"]
    clientes = db["clientes"]
    pedidos = db["pedidos"]
    conexao_ok = True

except Exception as erro:
    conexao_ok = False
    st.error(f"Erro ao conectar ao MongoDB: {erro}")


# CABEÇALHO
st.title("🛒 E-Shop Brasil")
st.subheader("Sistema de Gestão de Clientes e Pedidos")
st.markdown("---")


if conexao_ok:

    st.success("Conexão com MongoDB realizada com sucesso!")

    # MENU PRINCIPAL
    opcao = st.sidebar.selectbox(
        "Menu Principal",
        [
            "Início",
            "Cadastrar Clientes",
            "Cadastrar Pedidos",
            "Consultar Dados",
            "Relatórios"
        ]
    )

    # PÁGINA INICIAL
    if opcao == "Início":

        st.header("Bem-vindo ao E-Shop Brasil!")
        st.write(
            "Sistema de gestão desenvolvido com Python, "
            "Streamlit e MongoDB."
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Total de clientes",
            clientes.count_documents({})
        )

        col2.metric(
            "Total de pedidos",
            pedidos.count_documents({})
        )

    # CADASTRO DE CLIENTES
    elif opcao == "Cadastrar Clientes":

        st.header("👤 Cadastro de Clientes")

        with st.form("form_cliente"):

            nome = st.text_input("Nome completo")
            cpf = st.text_input("CPF")
            telefone = st.text_input("Telefone")
            email = st.text_input("E-mail")
            endereco = st.text_area("Endereço")

            enviar = st.form_submit_button("Salvar Cliente")

        if enviar:

            if nome and cpf and telefone and email and endereco:

                try:
                    cliente_existente = clientes.find_one(
                        {"cpf": cpf}
                    )

                    if cliente_existente:
                        st.warning("Este CPF já está cadastrado.")

                    else:
                        clientes.insert_one({
                            "nome": nome,
                            "cpf": cpf,
                            "telefone": telefone,
                            "email": email,
                            "endereco": endereco
                        })

                        st.success(
                            "Cliente cadastrado com sucesso!"
                        )

                except PyMongoError as erro:
                    st.error(f"Não foi possível salvar: {erro}")

            else:
                st.warning("Preencha todos os campos.")

    # CADASTRO DE PEDIDOS
    elif opcao == "Cadastrar Pedidos":

        st.header("📦 Cadastro de Pedidos")

        lista_clientes = list(
            clientes.find({}, {"nome": 1, "cpf": 1})
        )

        if lista_clientes:

            opcoes_clientes = {
                f'{c["nome"]} - CPF: {c["cpf"]}': c["_id"]
                for c in lista_clientes
            }

            with st.form("form_pedido"):

                cliente_escolhido = st.selectbox(
                    "Selecione o cliente",
                    list(opcoes_clientes.keys())
                )

                produto = st.text_input("Produto")

                quantidade = st.number_input(
                    "Quantidade",
                    min_value=1,
                    step=1
                )

                valor = st.number_input(
                    "Valor unitário (R$)",
                    min_value=0.0,
                    step=1.0
                )

                enviar_pedido = st.form_submit_button(
                    "Salvar Pedido"
                )

            if enviar_pedido:

                if produto and valor > 0:

                    try:
                        pedidos.insert_one({
                            "cliente_id": opcoes_clientes[
                                cliente_escolhido
                            ],
                            "produto": produto,
                            "quantidade": quantidade,
                            "valor_unitario": valor,
                            "valor_total": quantidade * valor,
                            "data": datetime.now()
                        })

                        st.success(
                            "Pedido cadastrado com sucesso!"
                        )

                    except PyMongoError as erro:
                        st.error(f"Erro ao salvar pedido: {erro}")

                else:
                    st.warning(
                        "Informe o produto e um valor maior que zero."
                    )

        else:
            st.info(
                "Cadastre um cliente antes de cadastrar pedidos."
            )

    # CONSULTA, EDIÇÃO E EXCLUSÃO
    elif opcao == "Consultar Dados":

        st.header("🔎 Consultar e Editar Clientes")

        aba1, aba2 = st.tabs(["Clientes", "Pedidos"])

        # ABA DE CLIENTES
        with aba1:

            st.subheader("Pesquisar Clientes")

            cpf_busca = st.text_input(
                "Digite o CPF para pesquisar"
            )

            if cpf_busca:
                lista_clientes = list(
                    clientes.find({
                        "cpf": {
                            "$regex": cpf_busca,
                            "$options": "i"
                        }
                    })
                )
            else:
                lista_clientes = list(clientes.find())

            if lista_clientes:

                for cliente in lista_clientes:

                    with st.expander(
                        f'{cliente["nome"]} - CPF: {cliente["cpf"]}'
                    ):

                        # FORMULÁRIO DE EDIÇÃO
                        with st.form(
                            f'editar_{cliente["_id"]}'
                        ):

                            nome = st.text_input(
                                "Nome completo",
                                value=cliente.get("nome", "")
                            )

                            cpf = st.text_input(
                                "CPF",
                                value=cliente.get("cpf", "")
                            )

                            telefone = st.text_input(
                                "Telefone",
                                value=cliente.get("telefone", "")
                            )

                            email = st.text_input(
                                "E-mail",
                                value=cliente.get("email", "")
                            )

                            endereco = st.text_area(
                                "Endereço",
                                value=cliente.get("endereco", "")
                            )

                            salvar = st.form_submit_button(
                                "Salvar alterações"
                            )

                        # SALVAR ALTERAÇÕES
                        if salvar:

                            if nome and cpf and telefone and email and endereco:

                                try:
                                    cpf_existente = clientes.find_one({
                                        "cpf": cpf,
                                        "_id": {"$ne": cliente["_id"]}
                                    })

                                    if cpf_existente:
                                        st.warning(
                                            "Este CPF pertence a outro cliente."
                                        )

                                    else:
                                        clientes.update_one(
                                            {"_id": cliente["_id"]},
                                            {
                                                "$set": {
                                                    "nome": nome,
                                                    "cpf": cpf,
                                                    "telefone": telefone,
                                                    "email": email,
                                                    "endereco": endereco
                                                }
                                            }
                                        )

                                        st.success(
                                            "Cliente atualizado com sucesso!"
                                        )

                                        st.rerun()

                                except PyMongoError as erro:
                                    st.error(
                                        f"Erro ao atualizar cliente: {erro}"
                                    )

                            else:
                                st.warning(
                                    "Preencha todos os campos."
                                )

                        # EXCLUSÃO COM CONFIRMAÇÃO
                        st.warning(
                            "A exclusão também apagará os pedidos "
                            "associados a este cliente."
                        )

                        confirmar = st.checkbox(
                            "Confirmo que desejo excluir este cliente "
                            "e seus pedidos.",
                            key=f'confirmar_{cliente["_id"]}'
                        )

                        if st.button(
                            "Excluir cliente",
                            key=f'excluir_{cliente["_id"]}',
                            disabled=not confirmar
                        ):

                            try:
                                pedidos.delete_many({
                                    "cliente_id": cliente["_id"]
                                })

                                clientes.delete_one({
                                    "_id": cliente["_id"]
                                })

                                st.success(
                                    "Cliente e seus pedidos excluídos!"
                                )

                                st.rerun()

                            except PyMongoError as erro:
                                st.error(
                                    f"Erro ao excluir cliente: {erro}"
                                )

            else:
                st.info("Nenhum cliente encontrado.")

        # ABA DE PEDIDOS
        with aba2:

            st.subheader("Pedidos cadastrados")

            dados_pedidos = list(
                pedidos.aggregate([
                    {
                        "$lookup": {
                            "from": "clientes",
                            "localField": "cliente_id",
                            "foreignField": "_id",
                            "as": "dados_cliente"
                        }
                    },
                    {
                        "$unwind": "$dados_cliente"
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "cliente": "$dados_cliente.nome",
                            "cpf": "$dados_cliente.cpf",
                            "produto": 1,
                            "quantidade": 1,
                            "valor_unitario": 1,
                            "valor_total": 1,
                            "data": 1
                        }
                    }
                ])
            )

            if dados_pedidos:
                st.dataframe(
                    dados_pedidos,
                    width="stretch"
                )
            else:
                st.info("Nenhum pedido cadastrado.")

    # RELATÓRIOS
    elif opcao == "Relatórios":

        st.header("📊 Relatórios")

        total_clientes = clientes.count_documents({})
        total_pedidos = pedidos.count_documents({})

        valor_total = list(
            pedidos.aggregate([
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$valor_total"}
                    }
                }
            ])
        )

        faturamento = (
            valor_total[0]["total"]
            if valor_total else 0
        )

        col1, col2, col3 = st.columns(3)

        col1.metric("Clientes", total_clientes)
        col2.metric("Pedidos", total_pedidos)

        col3.metric(
            "Faturamento",
            f"R$ {faturamento:.2f}"
        )

        st.markdown("---")

        st.subheader("📈 Gráfico de Faturamento")

        if faturamento > 0:
            st.bar_chart({
                "Faturamento (R$)": [faturamento]
            })
        else:
            st.info(
                "Ainda não existem vendas para exibir."
            )

else:
    st.warning(
        "Verifique a conexão e o arquivo .env "
        "antes de utilizar o sistema."
    )
