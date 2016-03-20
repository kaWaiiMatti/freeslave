import json
import logging

from bottle import Bottle, run, request, HTTPResponse, static_file
from freeslave import FreeSlave
from node import Node
from base_task import TaskPackage
from task_md5 import MD5HashTask, MD5HashPackage

logger = logging.getLogger(__name__)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    config = {'ip': 'localhost', 'port': 8080}
    try:
        with open('config.dat', mode='r') as f:
            custom_config = json.loads(f.read())
            for key in custom_config:
                config[key] = custom_config[key]
    except (IOError, KeyError, ValueError):
        pass

    fs = FreeSlave(config['ip'], config['port'])

    app = Bottle(autojson=True)

    @app.route('/')
    def get_client():
        return static_file('index.html', root='client/')

    @app.route('/<filename>')
    def get_static_file(filename):
        return static_file(filename, root='client/')

    # Another node request all known nodes.
    @app.route('/api/nodes')
    def get_all_nodes():
        nodes = []
        for node in fs.get_other_nodes():
            nodes.append(node.get_dict())
        return HTTPResponse(
            status=200,
            headers={'Content-Type': 'application/json'},
            body=json.dumps(nodes)
        )

    # Another node registers itself to this node.
    # Node ip and port are given in JSON format in body.
    @app.route('/api/nodes', method='POST')
    def register_node():
        # Verify data
        data = parse_request_payload(request)
        if type(data) == HTTPResponse:
            return data
        if not Node.validate_node_data(data):
            return HTTPResponse(
                status=400,
                body=json.dumps({'error': 'Invalid node information.'})
            )
        # Create known nodes response
        response_nodes = []
        for known_node in fs.get_other_nodes():
            known = False
            for node in data['nodes']:
                if Node(node) == known_node:
                    known = True
                    break
            if not known:
                response_nodes.append(known_node.get_dict())
        # ADD REGISTERING NODE
        fs.add_node(data)
        # Add given node to be registered if register parameter is given.
        # This is used when registering a new node from client.
        new_nodes = []
        try:
            if data['register']:
                new_nodes.append(Node(data))
        except KeyError:
            pass
        # LOOP LIST OF RECEIVED NODES AND TRY TO ADD THEM
        for node in data['nodes']:
            if fs.add_node(node):
                new_nodes.append(Node(node))
        # REGISTER TO NEW NODES
        for node in new_nodes:
            fs.register_to_node(node)
        return HTTPResponse(
            status=200,
            body=json.dumps({'nodes': response_nodes})
        )

    # Another node pings to test if server is up.
    @app.route('/api/nodes/ping')
    def node_keep_alive():
        return HTTPResponse(status=200)

    @app.route('/api/tasks')
    def get_all_tasks():
        tasks = []
        for task in fs.tasks:
            tasks.append(task.get_dict())
        return HTTPResponse(
            status=200,
            headers={'Content-Type': 'application/json'},
            body=json.dumps(tasks)
        )

    @app.route('/api/tasks', method='POST')
    def add_task():
        data = parse_request_payload(request)
        if type(data) == HTTPResponse:
            return data
        if MD5HashTask.validate_input(data):
            if fs.add_task(MD5HashTask(
                    ip=config['ip'],
                    port=config['port'],
                    target_hash=data['target_hash'],
                    max_length=data['max_length'],
                    task_id=fs.get_task_id())):
                fs.delegate_packages()
                return HTTPResponse(status=202)
            else:
                return HTTPResponse(
                    status=409,
                    body='Task with given id or similar '
                         'parameters already exists!'
                )

    @app.route('/api/tasks/<id:int>')
    def get_task(id):
        for task in fs.tasks:
            if task.task_id == id:
                return HTTPResponse(
                    status=200,
                    body=json.dumps(task.get_dict())
                )
        return HTTPResponse(status=404)

    @app.route('/api/tasks/<id:int>', method='DELETE')
    def delete_task(id):
        if fs.remove_task(id):
            return HTTPResponse(status=204)
        return HTTPResponse(status=404)

    @app.route('/api/packages/<ip>/<port:int>')
    def accept_packages(ip, port):
        data = {'ip': ip, 'port': port}
        if FreeSlave.validate_package_get_request(data):
            # TODO: calculate how many can be assigned to given ip & port
            # (max half of buffer should be assigned to single node!)
            body = {'available_buffer': fs.get_package_buffer_left()}
            return HTTPResponse(
                status=200,
                body=json.dumps(body)
            )
        return HTTPResponse(
            status=400,
            body=json.dumps(
                {
                    'error': 'Request did not pass validator! '
                             'Required values are ip(str) and port(int).'
                }
            )
        )

    @app.route('/api/packages', method='POST')
    def add_packages():
        data = parse_request_payload(request)
        if type(data) == HTTPResponse:
            return data
        received_packages = []
        if "packages" not in data.keys():
            return HTTPResponse(
                status=400,
                body="Invalid payload format"
            )
        for package in data["packages"]:
            if 'type' not in package.keys():
                return HTTPResponse(
                    status=400,
                    body='No type defined for package: {}'.format(package)
                )
            if package['type'] == 'md5hashpackage':
                if MD5HashPackage.validate_md5hashpackage_data(package):
                    received_packages.append(MD5HashPackage(package))
                else:
                    return HTTPResponse(
                        status=400,
                        body='Invalid or insufficient parameters '
                             'for md5hashpackage. Package: {}'.format(package)
                    )
            else:
                return HTTPResponse(
                    status=400,
                    body='Unknown package type.'
                )
        for package in received_packages:
            fs.add_package(package)
        for package in fs.packages:
            logger.debug(package)
        while fs.start_worker():
            logger.debug("Started worker.")
        logger.debug("Max worker amount reached.")
        return HTTPResponse(status=204)

    @app.route('/api/packages/<task_id:int>/<package_id:int>', method='POST')
    def receive_result(task_id, package_id):
        data = parse_request_payload(request)
        if type(data) == HTTPResponse:
            return data
        if 'type' not in data.keys():
            return HTTPResponse(
                status=400,
                body=json.dumps({'error': 'Type is not defined!'})
            )
            # TODO: check if task_id is valid, check if package id is valid,
            # check if does not have response and then add result, response 200
        if data['type'] == 'md5hashpackage':
            if not MD5HashPackage.validate_md5hashpackage_result(data):
                return HTTPResponse(
                    status=400,
                    body=json.dumps({'error': 'Data did not pass validator!'})
                )
            """
            elif data['type'] == 'another_package_type':
                if not Another_package_class.validate_result(data):
                    return HTTPResponse(
                        status=400,
                        body=json.dumps({'error': 'Data did not pass validator!'})
                    )
            """
        else:
            return HTTPResponse(
                status=400,
                body=json.dumps({'error': 'Unknown package type!'})
            )
        for task in fs.tasks:
            if task_id == task.task_id:
                task.add_result(identifier=package_id, data=data)
                return HTTPResponse(status=200)

        return HTTPResponse(
            status=404,
            body=json.dumps({'error': 'Could not find task with given id!'})
        )

    @app.route('/api/processes', method='POST')
    def register_worker():
        data = parse_request_payload(request)
        if type(data) == HTTPResponse:
            return data
        if not FreeSlave.validate_register_worker_data(data):
            return HTTPResponse(
                status=400,
                body=json.dumps(
                    {'error': 'Posted data did not pass validator.'}
                )
            )
        posted_package = TaskPackage(data)
        for package in fs.packages:
            if package == posted_package:
                package.set_process_id(data['process_id'])
                package.update_last_active()
                logger.debug(
                    'Worker count: {}'.format(fs.get_active_worker_count())
                )
                return HTTPResponse(status=204)
        return HTTPResponse(
            status=404,
            body=json.dumps(
                {'error': 'Could not find package with given parameters.'}
            )
        )

    @app.route('/api/processes/<process_id:int>', method='POST')
    def worker_keep_alive(process_id):
        for package in fs.packages:
            if package.process_id == process_id:
                package.update_last_active()
                return HTTPResponse(status=204)
        return HTTPResponse(
            status=404,
            body=json.dumps(
                {'error': 'Process with given process_id cannot be found!'}
            )
        )

    @app.route('/api/processes/<process_id:int>', method='DELETE')
    def unregister_worker(process_id):
        for package in fs.packages:
            if package.process_id == process_id:
                fs.packages.remove(package)
                return HTTPResponse(status=204)

        return HTTPResponse(
            status=404,
            body=json.dumps(
                {'error': 'Process with given process_id cannot be found!'}
            )
        )

    @app.route('/api/test', method='POST')
    def test():
        logger.debug(bytes.decode(request.body.read()))

    # OK, so this should be at the bottom. I feel so dirty having function
    # definitions inside main() and then having logic both at the top and
    # bottom...
    run(app, host=config['ip'], port=config['port'])


def parse_request_payload(r):
    try:
        data = json.loads(bytes.decode(r.body.read()))
    except ValueError:
        return HTTPResponse(
            status=400,
            body="Error parsing request JSON payload."
        )
    return data

if __name__ == "__main__":
    main()
