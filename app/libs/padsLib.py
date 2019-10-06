import requests
import xml.etree.ElementTree as ET
from localsecrets import urlPaDS, soapTest

authenticateMore = """<?xml version="1.0" encoding="utf-8"?>
                        <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                          <soap12:Body>
                            <AuthenticateUserAndReturnExtraInfo xmlns="http://localhost/PEPProduct/PEPProduct">
                                <UserName>{}</UserName>
                                <Password>{}</Password>
                            </AuthenticateUserAndReturnExtraInfo>                
                          </soap12:Body>
                      </soap12:Envelope>
"""

def authViaPaDS(username, password):
    """
    """
    retVal = None
    headers = {'content-type': 'text/xml'}
    ns = {"pepprod": "http://localhost/PEPProduct/PEPProduct"}
    soapMessage = authenticateMore.format(username, password)
    response = requests.post(urlPaDS, data=soapMessage, headers=headers)
    #print (response.content)
    root = ET.fromstring(response.content)
    # parse XML return
    AuthenticateUserAndReturnExtraInfoResultNode = root.find('.//pepprod:AuthenticateUserAndReturnExtraInfoResult', ns)
    productCodeNode = root.find('.//pepprod:ProductCode', ns)
    GatewayIdNode = root.find('.//pepprod:GatewayId', ns)
    SubscriberNameNode = root.find('.//pepprod:SubscriberName', ns)
    SubscriberEmailAddressNode = root.find('.//pepprod:SubscriberEmailAddress', ns)
    # assign data
    AuthenticateUserAndReturnExtraInfoResult = AuthenticateUserAndReturnExtraInfoResultNode.text
    if AuthenticateUserAndReturnExtraInfoResult:
        productCode = productCodeNode.text
        gatewayID = GatewayIdNode.text
        SubscriberName = SubscriberNameNode.text
        SubscriberEmailAddress = SubscriberEmailAddressNode.text
        
        refToCheck = "http://www.psychoanalystdatabase.com/PEPWeb/PEPWeb{}Gateway.asp".format(gatewayID)
        
        retVal = {
                    "authenticated" : AuthenticateUserAndReturnExtraInfoResult,
                    "username" : SubscriberName,
                    "userEmail" : SubscriberEmailAddress,
                    "gatewayID" : gatewayID,
                    "productCode" : productCode
                }
    
    print (retVal)

    return retVal
