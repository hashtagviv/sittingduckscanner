import asyncio
import threading
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from sittingduckscanner.utils.iterate_subdomains import subdomain_enumeration
import sittingduckscanner.utils.lame_delegation_check as lame_delegation_check
import sittingduckscanner.utils.compare_registrar_provider as registrar_check

from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_cors import cross_origin

app = Flask(__name__)

# Enable CORS for all domains and all API endpoints
CORS(app, resources={r"/api/*": {"origins": "localhost:3000"}}, supports_credentials=True)

aggregated_data = {}
file_lock = threading.Lock()
aggregated_data_lock = threading.Lock()

def generate_filename(domain):
    return domain + ".json"

def initialize_file(filename):
    with open(filename, 'w'):
        pass
    return filename

def write_to_file(filename, data):
    print('Writing to file...')
    with file_lock:
        with open(filename, 'a') as f:
            f.write(json.dumps(data) + "\n")

async def process_subdomain(subdomain: str, parent_response, filename):
   
    print(f'Processing subdomain {subdomain}')
    subdomain = subdomain.replace('www.', '')
    depth = subdomain.count('.') - 1
    try:
        with aggregated_data_lock:
            if subdomain in aggregated_data:
                print(f'{subdomain} already processed')
                raise Exception("Subdomain already processed")
    except:
        return
    registrar_dns_diff = registrar_check.process_data(
        subdomain, parent_response, aggregated_data
    )

    print(f'Starting lame delegation check for {subdomain}')
    lame_delegation, nameservers = lame_delegation_check.process_data(
        subdomain, aggregated_data
    )

    try:
        with aggregated_data_lock:
            print(f'Writing to cache {subdomain}')
            if subdomain in aggregated_data:
                print(f'{subdomain} already processed')
                raise Exception("Subdomain already processed")
            aggregated_data[subdomain] = {
                'depth': depth,
                'registrar_dns_different': registrar_dns_diff,
                'lame_delegation': lame_delegation,
                'flagged_name_servers': nameservers
            }
    except Exception as e:
        return
    write_to_file(filename, {subdomain: aggregated_data[subdomain]})

async def main(domain: str):
    filename = initialize_file(generate_filename(domain))
    executor = ThreadPoolExecutor(max_workers=10)
    parent_domain_dns_registrat_diff = registrar_check.check_if_different(domain, None)
    lame_delegation_answer, nameservers = lame_delegation_check.process_data(domain, aggregated_data)
    aggregated_data[domain] = {
        'distance': 0,
        'registrar_dns_different': parent_domain_dns_registrat_diff,
        'lame_delegation': lame_delegation_answer,
        'flagged_name_servers': nameservers
    }
    write_to_file(filename, {domain: aggregated_data[domain]})
    async for subdomain in subdomain_enumeration(domain):
        executor.submit(process_subdomain, subdomain, parent_domain_dns_registrat_diff, filename)

@app.after_request
def after_request(response):
    # Ensure CORS headers are added to every response
    response.headers['Access-Control-Allow-Origin'] = 'localhost:3000'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.route('/')
@cross_origin()
def index():
    return 'Flask server is running!'

@app.route('/api/domain-check/', methods=['POST', 'OPTIONS'])
def domain_check():
    try:
        if request.method == 'OPTIONS':
            # Handle the preflight OPTIONS request
            response = make_response(jsonify({'status': 'Preflight request received'}))
            response.headers['Access-Control-Allow-Origin'] = 'localhost:3000'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response, 200
        
        data = request.json
        domain = data.get('domain')

        if not domain:
            return jsonify({'error': 'Domain is required'}), 400

        parent_domain_dns_registrat_diff = registrar_check.check_if_different(domain, None)
        lame_delegation_answer, nameservers = lame_delegation_check.process_data(domain, aggregated_data)

        result = {
            'domain': domain,
            'registrar_dns_different': parent_domain_dns_registrat_diff,
            'lame_delegation': lame_delegation_answer,
            'flagged_nameservers': nameservers
        }

        return jsonify(result)
    except Exception as e:
        # Log the error and return a 403
        print(f"Error processing the domain-check request: {e}")
        return jsonify({'error': str(e)}), 403


@app.route('/api/subdomain-enumeration', methods=['POST', 'OPTIONS'])
async def subdomain_enumeration_api():
    if request.method == 'OPTIONS':
        # Handle the preflight OPTIONS request
        response = make_response(jsonify({'status': 'Preflight request received'}))
        response.headers['Access-Control-Allow-Origin'] = 'localhost:3000'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response, 200

    try:
        data = request.json
        domain = data.get('domain')

        if not domain:
            return jsonify({'error': 'Domain is required'}), 400

        subdomains = []
        async for subdomain in subdomain_enumeration(domain):
            subdomains.append(subdomain)

        return jsonify({'subdomains': subdomains})
    except Exception as e:
        print(f"Error processing subdomain enumeration: {e}")
        return jsonify({'error': str(e)}), 403


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("domain", type=str, help="The domain to enumerate")
    args = parser.parse_args()

    
    def run_flask():
        app.run(debug=True, use_reloader=False)

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    asyncio.run(main(args.domain))
