from bottle import Bottle, run, route, BaseRequest, FormsDict, request, HTTPResponse
from freeslave import FreeSlave
from node import Node
from task_md5 import Md5HashTask, Md5HashPackage
import os
import json

def main():
    #TODO: get as parameters or detect automatically?
    HOST = 'localhost'
    PORT = 8080

    fs = FreeSlave(HOST, PORT)

    app = Bottle()

    @app.route('/')
    def getClient():
        #TODO: implement client and return it here
        return "client here"

    #Another node request all known nodes.
    @app.route('/api/nodes')
    def getAllNodes():
        nodes = []
        for node in fs.getOtherNodes():
            nodes.append(node.getDict())
        return HTTPResponse(body=json.dumps(nodes), status=200)

    #Another node registers itself to this node.
    #Node ip and port are given in JSON format in body.
    @app.route('/api/nodes', method='POST')
    def registerNode():
        data = json.loads(bytes.decode(request.body.read()))
        if Node.validateNodeData(data):
            fs.addNode(data)
            #TODO: parse list of known nodes and add new ones. Register to new ones.
            #TODO: update known nodes list to drive
            print('Added new node {}:{}'.format(data['ip'], data['port']))
        return HTTPResponse(status=200)

    #Another node pings to test if server is up.
    @app.route('/api/nodes/ping')
    def nodeKeepAlive():
        return HTTPResponse(status=200)

    @app.route('/api/tasks')
    def getAllTasks():
        tasks = []
        for task in fs.tasks:
            tasks.append(task.getDict())
        return HTTPResponse(body=json.dumps(tasks), status=200)

    @app.route('/api/tasks', method='POST')
    def addTask():
        data = json.loads(bytes.decode(request.body.read()))
        if(Md5HashTask.validateMd5HashTaskData(data)):
            if fs.addTask(Md5HashTask(ip=HOST, port=PORT, target_hash=data['target_hash'], max_length=data['max_length'], task_id=fs.getTaskId())):
                #TODO: assign working packages
                pass
        for task in fs.tasks:
            print(task)
        return HTTPResponse(body='success', status=200)
        #TODO: check if task exists with given parameters. If not, add and start executing

    @app.route('/api/tasks/<id:int>')
    def getTask(id):
        for task in fs.tasks:
            if task.task_id == id:
                return HTTPResponse(body=json.dumps(task.getDict()), status=200)
        return HTTPResponse(status=404)


    @app.route('/api/packages')
    def acceptPackages():
        data = {'accept_packages':fs.getPackageBufferLeft()}
        HTTPResponse(body=json.dumps(data), status=200)

    @app.route('/api/packages', method='POST')
    def addPackages():
        data = json.loads(bytes.decode(request.body.read()))
        received_packages = []
        for package in data:
            if 'type' not in package.keys():
                return HTTPResponse(body='No type defined for package:{}'.format(package), status=400)
            if package['type'] == 'md5hashpackage':
                if(Md5HashPackage.validate_md5hashpackage_data(package)):
                    received_packages.append(Md5HashPackage(package))
                else:
                    return HTTPResponse(body='Invalid or insufficient parameters for m5hashpackage. Package:{}'.format(package), status=400)
            else:
                return HTTPResponse(body='Unknown package type.', status=400)
        for package in received_packages:
            fs.addPackage(package)
        for package in fs._packages:
            print(package)
        #TODO: start working on packages if not max worker amount!

    @app.route('/api/packages/<task_id:int>/<package_id:int>', method='POST')
    def receiveResult(task_id, package_id):
        #TODO: check if task_id is valid, check if package id is valid, check if does not have response and then add result, response 200
        pass

    @app.route('/api/processes', method='POST')
    def registerWorker():
        #TODO: check if current pid not in worker list and add if not. Set last connected time
        pass

    @app.route('/api/processes/<process_id:int>', method='POST')
    def workerKeepAlive():
        #TODO: update worker last connected time
        pass

    @app.route('/api/processes/<process_id:int>', method='DELETE')
    def unregisterWorker():
        #TODO: remove worker from worker list
        pass

    run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main()

'''

newpid = os.fork()
        if newpid == 0:
            for i in range(10):
                print('this works')
            os._exit(0)
        else:
            return ','.join(findPrimes(1000))

'''