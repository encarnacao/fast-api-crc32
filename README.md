# FastAPI CRC32 Calculator

Uma API simples utilizada para calcular o CRC32 de um arquivo PDF, com validação de tipo de arquivo.

## Dependências

- **fastapi[standard]** — framework web (inclui uvicorn)
- **pydantic-settings** — gerenciamento de configuração via variáveis de ambiente
- **python-multipart** — parsing de uploads multipart
- **structlog** — logging estruturado

### Desenvolvimento e testes

- **pytest** — framework de testes
- **httpx** — cliente HTTP async para testes de integração
- **pytest-asyncio** — suporte a testes assíncronos no pytest

## Configuração

As configurações são gerenciadas via variáveis de ambiente ou arquivo `.env`:

| Variável             | Padrão           | Descrição                     |
| -------------------- | ---------------- | ----------------------------- |
| `APP_NAME`           | `fast-api-crc32` | Nome da aplicação             |
| `APP_HOST`           | `0.0.0.0`        | Host de bind                  |
| `APP_PORT`           | `8000`           | Porta de bind                 |
| `LOG_LEVEL`          | `info`           | Nível de log                  |
| `ENVIRONMENT`        | `development`    | Nome do ambiente              |
| `MAX_UPLOAD_SIZE_MB` | `50`             | Tamanho máximo de upload (MB) |

## Executando com Docker

```bash
docker compose up
```

O compose monta o diretório `./app` no container e executa o uvicorn em modo `--reload` para desenvolvimento.

## Endpoints

### `GET /` — Health Check

Endpoint de health check que retorna uma mensagem simples.

**Resposta:**

```json
{ "message": "Hello, World!" }
```

Este endpoint existe apenas para teste da API. Ele foi incluído principalmente para testar o uso do **structlog**, pois eu queria ter logs estruturados no terminal mas nunca havia utilizado a biblioteca antes. A cada requisição neste endpoint, um log estruturado é emitido com informações como método HTTP, path, IP do cliente, user-agent e query params, o que serviu como um primeiro contato prático com a ferramenta.

### `POST /v1/calcular_crc` — Cálculo de CRC32

Recebe um arquivo PDF via upload multipart e retorna o checksum CRC32 do conteúdo.

**Request:** `multipart/form-data` com campo `file` contendo o arquivo PDF.

**Resposta (sucesso):**

```json
{
  "filename": "documento.pdf",
  "size": 102400,
  "status": "received",
  "crc32": 3456789012
}
```

O valor `crc32` é um inteiro sem sinal de 32 bits, calculado com `zlib.crc32`.

## Validação do arquivo PDF

Antes de calcular o CRC32, o arquivo enviado passa por três etapas de validação, implementadas como uma dependência FastAPI (`Depends`). Todas as falhas retornam HTTP **422 Unprocessable Entity**.

### 1. Extensão do arquivo

O nome do arquivo deve terminar com `.pdf` (case-insensitive). Se o arquivo não tiver nome ou a extensão for diferente, a requisição é rejeitada.

> `"Uploaded file must have a .pdf extension"`

### 2. Content-Type

O campo `content_type` do upload deve ser exatamente `application/pdf`. Isso valida o tipo MIME declarado pelo cliente no momento do envio.

> `"Content type must be application/pdf, got {content_type}"`

### 3. Magic bytes (assinatura do arquivo)

Os primeiros 5 bytes do conteúdo do arquivo são lidos e comparados com `%PDF-`, que é a assinatura padrão presente no início de todo arquivo PDF válido. Essa verificação garante que o conteúdo real do arquivo é de fato um PDF, independentemente da extensão ou do content-type informado.

> `"File content does not appear to be a valid PDF"`

Se todas as validações passam, o cursor do arquivo é reposicionado no início (`seek(0)`) para que o handler da rota possa ler o conteúdo completo e calcular o CRC32.

## Logging

A aplicação utiliza **structlog** com renderização para console (`ConsoleRenderer`), integrado ao módulo `logging` da stdlib do Python. Os logs incluem timestamp ISO-8601, nível de log e campos estruturados específicos de cada evento (ex: `filename`, `client_ip`, `crc32_value`). Eventos de falha na validação do PDF são registrados com nível `warning`.

## Testes

O projeto inclui testes unitários e de integração utilizando **pytest**, **httpx** e **pytest-asyncio**. Para executar:

```bash
python -m pytest tests/ -v
```

### Testes unitários — `validate_pdf`

Testam a dependência de validação de PDF diretamente, cobrindo cada etapa de validação:

| Teste | Cenário |
| ----- | ------- |
| `test_rejects_wrong_extension` | Arquivo com extensão `.txt` é rejeitado (422) |
| `test_rejects_missing_filename` | Arquivo sem nome é rejeitado (422) |
| `test_rejects_wrong_content_type` | Content-type `text/plain` é rejeitado (422) |
| `test_rejects_invalid_magic_bytes` | Conteúdo sem a assinatura `%PDF-` é rejeitado (422) |
| `test_accepts_valid_pdf` | PDF válido passa na validação e o cursor é reposicionado no início |

### Testes de integração — `POST /v1/calcular_crc`

Testam o endpoint completo através do `httpx.AsyncClient` com a aplicação FastAPI:

| Teste | Cenário |
| ----- | ------- |
| `test_valid_pdf_returns_correct_crc` | Upload de PDF válido retorna CRC32 correto, filename, size e status |
| `test_invalid_file_returns_422` | Upload de arquivo inválido retorna HTTP 422 |
