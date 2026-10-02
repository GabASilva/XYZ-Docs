import json, os, uuid, datetime, boto3
from botocore.config import Config
from botocore.exceptions import ClientError

B = os.environ['BUCKET']; R = os.environ['ROLE_ARN']; K = os.environ['KMS_KEY_ARN']; REG = os.environ['AWS_REGION']
TIPOS = {'application/pdf': 'pdf', 'image/png': 'png', 'image/jpeg': 'jpg'}
sts = boto3.client('sts')


def s3_do_usuario(sub):
    # Credencial de 15 min que so alcanca o prefixo do usuario (session policy)
    p = f'usuario-{sub}'
    pol = {'Version': '2012-10-17', 'Statement': [
        {'Effect': 'Allow', 'Action': ['s3:GetObject', 's3:PutObject', 's3:RestoreObject'], 'Resource': f'arn:aws:s3:::{B}/{p}/*'},
        {'Effect': 'Allow', 'Action': 's3:ListBucket', 'Resource': f'arn:aws:s3:::{B}', 'Condition': {'StringLike': {'s3:prefix': f'{p}/*'}}},
        {'Effect': 'Allow', 'Action': ['kms:GenerateDataKey', 'kms:Decrypt'], 'Resource': K}]}
    c = sts.assume_role(RoleArn=R, RoleSessionName=f'u-{sub}', Policy=json.dumps(pol), DurationSeconds=900)['Credentials']
    s3 = boto3.client('s3', region_name=REG, endpoint_url=f'https://s3.{REG}.amazonaws.com',
                      aws_access_key_id=c['AccessKeyId'], aws_secret_access_key=c['SecretAccessKey'], aws_session_token=c['SessionToken'],
                      config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'}))
    return p, s3


def r(code, body):
    return {'statusCode': code, 'headers': {'content-type': 'application/json'}, 'body': json.dumps(body, default=str)}


def handler(event, ctx):
    sub = event['requestContext']['authorizer']['jwt']['claims']['sub']  # identidade vem do token, nunca do corpo
    rota = event['routeKey']; q = event.get('queryStringParameters') or {}
    p, s3 = s3_do_usuario(sub)

    if rota == 'POST /upload-url':
        b = json.loads(event.get('body') or '{}'); ct = b.get('contentType')
        if ct not in TIPOS:
            return r(400, {'erro': 'tipo de arquivo nao permitido'})
        key = f'{p}/{datetime.date.today().year}/{uuid.uuid4()}.{TIPOS[ct]}'
        f = {'Content-Type': ct}; c = [{'Content-Type': ct}, ['content-length-range', 1, 20 * 1024 * 1024]]
        if b.get('simularAntigo'):  # demo: grava direto em Deep Archive, como se tivesse +365 dias
            f['x-amz-storage-class'] = 'DEEP_ARCHIVE'; c.append({'x-amz-storage-class': 'DEEP_ARCHIVE'})
        return r(200, {'key': key, 'post': s3.generate_presigned_post(B, key, Fields=f, Conditions=c, ExpiresIn=900)})

    if rota == 'GET /files':
        objs = s3.list_objects_v2(Bucket=B, Prefix=p + '/').get('Contents', [])
        return r(200, [{'key': o['Key'], 'tamanho': o['Size'], 'classe': o['StorageClass'], 'data': o['LastModified']} for o in objs])

    key = q.get('key', '')
    # 1a camada: checagem da aplicacao. APP_CHECK=false simula um bug (IDOR) para provar a 2a camada.
    if os.environ.get('APP_CHECK', 'true') == 'true' and not key.startswith(p + '/'):
        return r(403, {'camada': 'aplicacao', 'erro': 'chave fora do seu prefixo'})

    if rota == 'GET /download-url':
        url = s3.generate_presigned_url('get_object', Params={'Bucket': B, 'Key': key}, ExpiresIn=300)
        try:
            h = s3.head_object(Bucket=B, Key=key)
        except ClientError as e:  # 2a camada: a credencial escopada nao alcanca outro prefixo
            return r(200, {'url': url, 'aviso': 'S3 negou o HEAD: ' + e.response['Error']['Code']})
        if h.get('StorageClass') == 'DEEP_ARCHIVE' and 'ongoing-request="false"' not in h.get('Restore', ''):
            return r(409, {'status': 'arquivado', 'restore': h.get('Restore', 'nao solicitado')})
        return r(200, {'url': url})

    if rota == 'POST /restore':
        try:
            s3.restore_object(Bucket=B, Key=key, RestoreRequest={'Days': 3, 'GlacierJobParameters': {'Tier': 'Standard'}})
        except ClientError as e:
            return r(409, {'erro': e.response['Error']['Code']})
        return r(202, {'status': 'restauracao solicitada (ate 12 h no tier Standard)'})

    return r(404, {'erro': 'rota desconhecida'})
