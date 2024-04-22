import sys
import json

DRM_DB_NAME = "./db/drm_db.json"

class Releases:
    def check_release_by_id_and_connection_name(id, connection_name):
        """ Checks if active release & connection name exist in the system
        :param id: Release ID
        :param connection_name: Connection name
        :return: JSON
        """
        verified_release_id = "null"
        verified_connection_id = "null"
        _connection_id = 0

        drm_db = json.loads(open(DRM_DB_NAME).read())
        for release in drm_db['releases']:
            if ("is_active" in release):
                is_active = release['is_active']
            else:
                is_active = True
            if (is_active and release['id'] == int(id)):
                verified_release_id = release['id']
                if ('solutions' in release):
                    for solution in release['solutions']:
                        if ("is_active" in solution):
                            is_active = solution['is_active']
                        else:
                            is_active = True
                        if(is_active):
                            if ('connections' in solution):
                                for connection in solution['connections']:
                                    _connection_id += 1
                                    if ("is_active" in connection):
                                        is_active = connection['is_active']
                                    else:
                                        is_active = True
                                    if (is_active and connection['name'] == connection_name):
                                        verified_connection_id = _connection_id

        js_text = '{"release_id": ' + str(verified_release_id) + ', "connection_id": ' + str(verified_connection_id) + '}'
        js = json.loads(js_text)
        return json.dumps(js)

    def get_release_by_id(id, release_obj):
        """ Return release details by release_id
        :param id: Release ID
        :param release_obj: Release object
        :return: JSON
        """
        drm_db = json.loads(open(DRM_DB_NAME).read())
        for release in drm_db['releases']:
            if (release['id'] == int(id)):
                release_obj.id = release['id']    
                release_obj.name = release['name']    
                release_obj.max_retries = release['max_retries']
                if  ("is_active" in release):   
                    release_obj.is_active = release['is_active'] 
                else:
                    release_obj.is_active = True
        js = json.loads(json.dumps(release_obj.__dict__))
        return json.dumps(js)

class Solutions:
    def get_solutions_by_release_id(release_id, solution_obj):
        """ Return solutions list details by release_id
        :param release_id: Release ID
        :param solution_obj: Solution object
        :return: JSON
        """
        _solution_id = 0
        js = json.loads('{"solutions":[]}')
        drm_db = json.loads(open(DRM_DB_NAME).read())
        for release in drm_db['releases']:
            if (release['id'] == release_id):
                verified_release_id = release['id']
                if ("solutions" in release):
                    for solution in release['solutions']:
                        _solution_id += 1
                        if ("is_active" in solution):
                            is_active = solution['is_active']
                        else:
                            is_active = True
                        if(is_active):
                            solution_obj.id = _solution_id    
                            solution_obj.name = solution['name']    
                            solution_obj.release_id = release_id 
                            if  ("ordinal" in solution):
                                solution_obj.ordinal = solution['ordinal'] 
                            else:
                                solution_obj.ordinal = _solution_id
                            solution_obj.solution_type_id = solution['solution_type_id']    
                            solution_obj.path = solution['path']   
                            if  ("is_active" in solution):
                                solution_obj.is_active = solution['is_active'] 
                            else:
                                solution_obj.is_active = True
                            solution_js = json.loads(json.dumps(solution_obj.__dict__))
                            js['solutions'].append(solution_js)
        return json.dumps(js)

class Connections:
    def get_connection_by_solution_id_and_name(release_id, solution_id, name, connection_obj):
        """ Return solution connection details by solution_id and name
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param name: Connection name
        :param connection_obj: Connection object
        :return: JSON
        """
        _solution_id = 0
        _connection_id = 0
        js = json.loads('{"connections":[]}')
        drm_db = json.loads(open(DRM_DB_NAME).read())
        for release in drm_db['releases']:
            if (release['id'] == int(release_id)):
                verified_release_id = release['id']
                if ("solutions" in release):
                    for solution in release['solutions']:
                        _solution_id += 1
                        if (int(solution_id) == _solution_id):
                            if ("connections" in solution):
                                for connection in solution['connections']:
                                    _connection_id += 1
                                    if(connection['name'] == name):
                                        connection_obj.id = _connection_id    
                                        connection_obj.name = connection['name']    
                                        connection_obj.solution_id = solution_id    
                                        connection_obj.connection_type_id = connection['connection_type_id']    
                                        connection_obj.connection_string = connection['connection_string']
                                        if ("is_active" in connection):   
                                            connection_obj.is_active = connection['is_active'] 
                                        else:
                                            connection_obj.is_active = True
                                        connection_js = json.loads(json.dumps(connection_obj.__dict__))
                                        js['connections'].append(connection_js)
        return json.dumps(js)

class SqlScriptsVariables:
    def get_sql_scripts_variables_by_solution_id(release_id, solution_id, sql_script_variable_obj):
        """ Return solution sql_scripts_variables details by solution_id
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param sql_script_variable_obj: Sql_Scripts_Variable object
        :return: JSON
        """
        _solution_id = 0
        _sql_script_variable_id = 0
        js = json.loads('{"sql_scripts_variables":[]}')
        drm_db = json.loads(open(DRM_DB_NAME).read())
        for release in drm_db['releases']:
            if (release['id'] == int(release_id)):
                verified_release_id = release['id']
                if ("solutions" in release):
                    for solution in release['solutions']:
                        _solution_id += 1
                        if (int(solution_id) == _solution_id):
                            if ("sql_scripts_variables" in solution):
                                for sql_script_variable in solution['sql_scripts_variables']:
                                    _sql_script_variable_id += 1
                                    sql_script_variable_obj.id = _sql_script_variable_id    
                                    sql_script_variable_obj.name = sql_script_variable['name']    
                                    sql_script_variable_obj.solution_id = solution_id    
                                    sql_script_variable_obj.value = sql_script_variable['value']    
                                    sql_script_variable_js = json.loads(json.dumps(sql_script_variable_obj.__dict__))
                                    js['sql_scripts_variables'].append(sql_script_variable_js)
        return json.dumps(js)

class SqlScripts:
    def get_sql_scripts_by_solution_id(release_id, solution_id, sql_script_obj):
        """ Return solution sql_scripts details by solution_id
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param sql_script_obj: Sql_Script object
        :return: JSON
        """
        js = json.loads('{"sql_scripts":[]}')
        drm_db = Db(DRM_DB_NAME)
        sql_command = "select id, name, solution_id, sql_text from sql_scripts where solution_id = {sol_id} order by id;".format(sol_id = solution_id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            sql_script_obj.id = row[0]    
            sql_script_obj.name = row[1]    
            sql_script_obj.solution_id = row[2]    
            sql_script_obj.sql_text = row[3]    
            sql_script_js = json.loads(json.dumps(sql_script_obj.__dict__))
            js['sql_scripts'].append(sql_script_js)
        return json.dumps(js)

class Projects:
    def get_projects_by_solution_id(release_id, solution_id, project_obj):
        """ Return solution projects details by solution_id
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param project_obj: Project object
        :return: JSON
        """
        js = json.loads('{"projects":[]}')
        drm_db = Db(DRM_DB_NAME)
        sql_command = "select projects.id, projects.name, projects.solution_id, projects.ordinal, targets_compare_db, targets_type_id, targets_list, targets_sql_script_id, sql_scripts.sql_text as targets_sql_text, max_degree_in_parallel, timeout_in_min, sleep_time_in_sec, fail_on_error, is_active from projects left join sql_scripts on projects.solution_id = sql_scripts.solution_id and projects.targets_sql_script_id = sql_scripts.id where projects.solution_id = {sol_id} order by projects.ordinal, projects.id;".format(sol_id = solution_id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            project_obj.id = row[0]    
            project_obj.name = row[1]    
            project_obj.solution_id = row[2]    
            project_obj.ordinal = row[3]    
            project_obj.targets_compare_db = row[4]    
            project_obj.targets_type_id = row[5]    
            project_obj.targets_list = row[6]    
            project_obj.targets_sql_script_id = row[7]    
            project_obj.targets_sql_text = row[8]    
            project_obj.max_degree_in_parallel = row[9]    
            project_obj.timeout_in_min = row[10]    
            project_obj.sleep_time_in_sec = row[11]    
            project_obj.fail_on_error = row[12]    
            project_obj.is_active = row[13]    
            project_js = json.loads(json.dumps(project_obj.__dict__))
            js['projects'].append(project_js)
        return json.dumps(js)

