from bottle import Bottle, run, route, BaseRequest, FormsDict, request, HTTPResponse, static_file
from freeslave import FreeSlave
from node import Node
from task_md5 import Md5HashTask, Md5HashPackage
import json

def main():
    config = {'ip':'localhost', 'port':8080}
    try:
        f = open('config.dat', mode='r')
        data = json.loads(f.read())
        for key in data:
            config[key] = data[key]
    except:
        pass

    fs = FreeSlave(config['ip'], config['port'])

    app = Bottle(autojson=True)

    @app.route('/')
    def get_client():
        return static_file('index.html', root='client/')

    @app.route('/<filename>')
    def get_static_file(filename):
        return static_file(filename, root='client/')

    #Another node request all known nodes.
    @app.route('/api/nodes')
    def getAllNodes():
        nodes = []
        for node in fs.getOtherNodes():
            nodes.append(node.getDict())
        return HTTPResponse(body=json.dumps(nodes), status=200, headers={'Content-Type':'application/json'})

    #Another node registers itself to this node.
    #Node ip and port are given in JSON format in body.
    @app.route('/api/nodes', method='POST')
    def registerNode():
        #Verify data
        data = json.loads(bytes.decode(request.body.read()))
        if not Node.validateNodeData(data):
            return HTTPResponse(body=json.dumps({'error':'Invalid node information.'}), status=400)
        #Create known nodes response
        response_nodes = []
        for known_node in fs.getOtherNodes():
            known = False
            for node in data['nodes']:
                if Node(node) == known_node:
                    known = True
                    break
            if not known:
                response_nodes.append(known_node.getDict())
        #ADD REGISTERING NODE
        fs.addNode(data)
        #LOOP LIST OF RECEIVED NODES AND TRY TO ADD THEM
        new_nodes = []
        for node in data['nodes']:
            if fs.addNode(node):
                new_nodes.append(Node(node))
        #REGISTER TO NEW NODES
        for node in new_nodes:
            fs.register_to_node(node)
        return HTTPResponse(body=json.dumps({'nodes':response_nodes}), status=200)

    #Another node pings to test if server is up.
    @app.route('/api/nodes/ping')
    def nodeKeepAlive():
        return HTTPResponse(status=200)

    @app.route('/api/tasks')
    def getAllTasks():
        tasks = []
        for task in fs.tasks:
            tasks.append(task.getDict())
        return HTTPResponse(body=json.dumps(tasks), status=200, headers={'Content-Type':'application/json'})

    @app.route('/api/tasks', method='POST')
    def addTask():
        data = json.loads(bytes.decode(request.body.read()))
        if(Md5HashTask.validateMd5HashTaskData(data)):
            if fs.addTask(Md5HashTask(ip=config['ip'], port=config['port'], target_hash=data['target_hash'], max_length=data['max_length'], task_id=fs.getTaskId())):
                #TODO: assign working packages
                return HTTPResponse(status=202)
            else:
                return HTTPResponse(body='Task with given id or similar parameters already exists!', status=409)
        for task in fs.tasks:
            print(task)
        return HTTPResponse(status=200)
        #TODO: check if task exists with given parameters. If not, add and start executing

    @app.route('/api/tasks/<id:int>')
    def getTask(id):
        for task in fs.tasks:
            if task.task_id == id:
                return HTTPResponse(body=json.dumps(task.getDict()), status=200)
        return HTTPResponse(status=404)

    @app.route('/api/tasks/<id:int>', method='DELETE')
    def deleteTask(id):
        if fs.removeTask(id):
            return HTTPResponse(status=204)
        return HTTPResponse(status=404)

    @app.route('/api/packages/<ip>/<port:int>')
    def acceptPackages(ip, port):
        data = {'ip':ip, 'port':port}
        if FreeSlave.validate_package_get_request(data):
            #TODO: calculate how many can be assigned to given ip & port (max half of buffer should be assigned to single node!)
            body = {'accept_packages':fs.getPackageBufferLeft()}
            return HTTPResponse(body=json.dumps(body), status=200)
        return HTTPResponse(body=json.dumps({'error':'Request did not pass validator! Required values are ip(str) and port(int).'}), status=400)

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
        data = json.loads(bytes.decode(request.body.read()))
        if 'type' not in data.keys():
            return HTTPResponse(body=json.dumps({'error':'Type is not defined!'}), status=400)
            #TODO: check if task_id is valid, check if package id is valid, check if does not have response and then add result, response 200
        if data['type'] == 'md5hashpackage':
            if not Md5HashPackage.validate_md5hashpackage_result(data):
                return HTTPResponse(body=json.dumps({'error':'Data did not pass validator!'}), status=400)
        #elif  data['type'] == 'another_package_type':
        #    if not Another_package_class.validate_result(data):
        #        return HTTPResponse(body=json.dumps({'error':'Data did not pass validator!'}), status=400)
        else:
            return HTTPResponse(body=json.dumps({'error':'Unknown package type!'}), status=400)
        for task in fs.tasks:
            if task_id == task.task_id:
                task.add_result(identifier=package_id, data=data)
                return HTTPResponse(status=200)

        return HTTPResponse(body=json.dumps({'error':'Could not find task with given id!'}), status=404)

    @app.route('/api/processes', method='POST')
    def registerWorker():
        data = json.loads(bytes.decode(request.body.read()))
        if not FreeSlave.validate_register_worker_data(data):
            return HTTPResponse(body=json.dumps({'error':'Posted data did not pass validator.'}), status=400)
        for package in fs._packages:
            if package.task_id == data['task_id'] and package.start_string == data['package_identifier'] and package.assigner_ip == data['assigner_ip'] and package.assigner_port == data['assigner_port']:
                package.set_process_id(data['process_id'])
                package.update_last_active()
                print('Worker count:{}'.format(fs.get_active_worker_count()))
                return HTTPResponse(status=204)
        return HTTPResponse(body=json.dumps({'error':'Could not find package with given parameters.'}), status=404)

    @app.route('/api/processes/<process_id:int>', method='POST')
    def workerKeepAlive(process_id):
        for package in fs._packages:
            if package.process_id == process_id:
                package.update_last_active()
                return HTTPResponse(status=204)
        return HTTPResponse(body=json.dumps({'error':'Process with given process_id cannot be found!'}), status=404)

    @app.route('/api/processes/<process_id:int>', method='DELETE')
    def unregisterWorker(process_id):
        for package in fs._packages:
            if package.process_id == process_id:
                fs._packages.remove(package)
                return HTTPResponse(status=204)
        return HTTPResponse(body=json.dumps({'error':'Process with given process_id cannot be found!'}), status=404)

    @app.route('/api/test', method='POST')
    def test():
        fs.delegate_packages()
        fs.start_worker()


    run(app, host=config['ip'], port=config['port'])

if __name__ == "__main__":
    main()