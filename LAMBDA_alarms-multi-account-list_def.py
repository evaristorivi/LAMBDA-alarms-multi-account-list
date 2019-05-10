#!/usr/bin/python
# -*- coding: utf-8 -*-

# alarms-multi-account-list-Lambda
# Evaristo R. Rivieccio Vega - Cloud, Middleware y Sistemas - L1
# evaristorivieccio@gmail.com

import boto3
import datetime
import pickle

# CONFIG
######################################################
######################################################

# CONFIG del seguimiento de errores de la Lambda
EMAIL_ERRORES_EMISOR = '<email_emisor>'
EMAIL_ERRORES_RECEPTOR = '<email_receptor>'

# CONFIG de S3
BUCKET = '<nombre del bucket, no el arn, sino el nombre>'
FICHERO_DATOS = '<nombre_fichero.pkl>'


# AÑADIR MÁS CUENTAS:
ACCOUNT_LIST = [
        {       'RoleArn' : "<arn role>",                                   #No olvidar las comas
                "RoleSessionName" : "<nombre-sesión>"
        },                                                                  #No olvidar las comas
        {
                'RoleArn' : "<arn role>",
                "RoleSessionName" : "<nombre-sesión>"
        },
#        {
#                'RoleArn' : "<arn role>",
#                "RoleSessionName" : "<nombre-sesión>"
#        },
#        {
#                'RoleArn' : "<arn role>",
#                "RoleSessionName" : "<nombre-sesión>"
#        }
#
#
]

######################################################
######################################################

#Guarda objetos
def save_obj(obj, name ):
    with open('/tmp/'+ name, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
        
# Seguimiento de errores la Lambda
def send_email(email_subject, email_body):
        ses = boto3.client('ses')
        email_from = EMAIL_ERRORES_EMISOR
        email_to = EMAIL_ERRORES_RECEPTOR
        email_subject = email_subject
        email_body = email_body
        response = ses.send_email(
            Source = email_from,
            Destination = {
                'ToAddresses': [
                    email_to,
                ]
            },
            Message = {
                'Subject': {
                    'Data': email_subject
                },
                'Body': {
                    'Text': {
                        'Data': email_body
                    }
                }
            }
        )
 

def lambda_handler(event, context):
        try:
                # Cliente STS
                sts_client = boto3.client('sts')
                # Cliente s3
                s3 = boto3.resource('s3')
        
                for allacounts in ACCOUNT_LIST:
                        assumed_role_object=sts_client.assume_role(
                                RoleArn=allacounts['RoleArn'],
                                RoleSessionName=allacounts['RoleSessionName']
                        )
        
                # Obtención de las credenciales temporales
                credentials = assumed_role_object['Credentials']
                
                cloudwatch_resource = boto3.resource(
                        'cloudwatch',   
                        aws_access_key_id=credentials['AccessKeyId'],
                        aws_secret_access_key=credentials['SecretAccessKey'],
                        aws_session_token=credentials['SessionToken'],
                )
        
                # Acceso al cliente de bajo nivel
                cloudwatchalarms = cloudwatch_resource.meta.client
                
                # Obtenemos las alarmas con su respectivo estado
                paginator = cloudwatchalarms.get_paginator('describe_alarms')
                
                # Guardamos el diccionario en un fichero
                for response in paginator.paginate():
                        save_obj(response,FICHERO_DATOS)
        
                # Subimos el fichero a s3
                s3.Bucket(BUCKET).upload_file('/tmp/' + FICHERO_DATOS, FICHERO_DATOS)
                
        except:
                # Control de errores de la Lambda::
                send_email("[LAMBDA NOMBRE DE LA LAMBDA... - FAILURE]", "La Lambda NOMBRE DE LA LAMBDA... se ha lanzado con errores.")