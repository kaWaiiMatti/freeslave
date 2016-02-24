from bottle import Bottle, run, route, BaseRequest, FormsDict, request, HTTPResponse
from freeslave import FreeSlave
from node import Node
import os
import json

def main():
    HOST = 'localhost'
    PORT = 8080

    fs = FreeSlave(HOST, PORT)

    app = Bottle()

    @app.route('/')
    def getClient():
        #TODO: implement client and return it here
        return "client here"

    @app.route('/api/nodes')
    def getAllNodes():
        #TODO: return json array of known nodes, not including this
        pass

    @app.route('/api/nodes', method='POST')
    def registerNode():
        data = json.loads(bytes.decode(request.body.read()))
        if Node.validateNodeData(data):
            fs.addNode(data)
        return HTTPResponse(status=200)

    @app.route('/api/nodes/ping')
    def nodeKeepAlive():
        #TODO: response 200
        pass

    @app.route('/api/tasks')
    def getAllTasks():
        #TODO: response json array of all tasks
        pass

    @app.route('/api/tasks', method='POST')
    def addTask():
        #TODO: check if task exists with given parameters. If not, add and start executing
        pass

    @app.route('/api/tasks/<id:int>')
    def getTask(id):
        #TODO: get task information based on id and return it
        pass

    @app.route('/api/packages')
    def acceptPackages():
        #TODO: return amount of working packages node accepts in json format
        pass

    @app.route('/api/packages', method='POST')
    def addPackages():
        #TODO: add working packages to buffer and start executing if not max worker amount
        pass


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