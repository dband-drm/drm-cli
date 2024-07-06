import sys
import json
import logging
from modules import sqlite, drm_logger

class Db:

    logger = drm_logger.configure_logging("parser_sqlite_json.Db")

    @drm_logger.log_decorator(logger) 
    def __init__(self, db_name = ""):   
        """ 
        Constructor
        :param db_name: SQLite databae name
        :return:
        """
        self.db_name = db_name

    @drm_logger.log_decorator(logger) 
    def select_query(self, query):    
        """ 
        Run SQL query & return result
        :param query: SQL Query
        :return: result
        """
        conn = sqlite.create_connection(self.db_name)
        rows = sqlite.execute_query(conn, query)
        sqlite.close_connection(conn)
        return rows
    
    @drm_logger.log_decorator(logger) 
    def execute_command(self, command):    
        """ 
        Run SQL command 
        :param command: SQL command
        :return: result
        """
        conn = sqlite.create_connection(self.db_name)
        sqlite.execute_command(conn, command)
        sqlite.close_connection(conn)


class Releases:

    logger = drm_logger.configure_logging("parser_sqlite_json.Releases")

    @drm_logger.log_decorator(logger) 
    def check_release_by_id_and_connection_name(db_file_name, id, connection_name):
        """ 
        Checks if active release & connection name exist in the system
        :param db_file_name: Database file name
        :param id: Release ID
        :param connection_name: Connection name
        :return: release ID & Connection ID (JSON)
        """
        drm_db = Db(db_file_name)
        #======================================
        # Get Release & Connection IDs by input
        #======================================
        sql_command = "select releases.id as release_id, connections.id as connection_id from releases left join solutions on solutions.release_id = releases.id and solutions.is_active = 1 left join connections on connections.solution_id = solutions.id and connections.name = '{conn_name}' and connections.is_active = 1 where releases.id = {rel_id} and releases.is_active = 1;".format(rel_id = id, conn_name = connection_name)
        rows = drm_db.select_query(sql_command)
        # Data found
        if(len(rows) > 0):
            for row in rows:
                verified_release_id = row[0]
                verified_connection_id = row[1] 
                if (verified_connection_id    == None):
                    verified_connection_id = "null"
        # No Data found
        else:
            verified_release_id = "null"
            verified_connection_id = "null"
            
        js_text = '{"release_id": ' + str(verified_release_id) + ', "connection_id": ' + str(verified_connection_id) + '}'
        js = json.loads(js_text)
        return json.dumps(js)

    @drm_logger.log_decorator(logger) 
    def get_release_by_id(db_file_name, id, release_obj):
        """ 
        Return release details by release_id
        :param db_file_name: Database file name
        :param id: Release ID
        :param release_obj: Release object
        :return: Release info (JSON)
        """
        drm_db = Db(db_file_name)
        #=======================
        # Get Release info by ID
        #=======================
        sql_command = "select id, name, max_retries, is_active from releases where id = {rel_id};".format(rel_id = id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            release_obj.id = row[0]    
            release_obj.name = row[1]    
            release_obj.max_retries = row[2]    
            release_obj.is_active = row[3] 
        js = json.loads(json.dumps(release_obj.__dict__))
        return json.dumps(js)

class Solutions:

    logger = drm_logger.configure_logging("parser_sqlite_json.Solutions")

    @drm_logger.log_decorator(logger) 
    def get_solutions_by_release_id(db_file_name, release_id, solution_obj):
        """ 
        Return solutions list details by release_id
        :param db_file_name: Database file name
        :param release_id: Release ID
        :param solution_obj: Solution object
        :return: Solution info (JSON)
        """
        js = json.loads('{"solutions":[]}')
        drm_db = Db(db_file_name)
        #=================================
        # Get Solutions info by Release ID
        #=================================
        sql_command = "select id, name, release_id, ordinal, solution_type_id, path, is_active from solutions where release_id = {rel_id} order by ordinal, id;".format(rel_id = release_id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            solution_obj.id = row[0]    
            solution_obj.name = row[1]    
            solution_obj.release_id = row[2]    
            solution_obj.ordinal = row[3]    
            solution_obj.solution_type_id = row[4]    
            solution_obj.path = row[5]    
            solution_obj.is_active = row[6] 
            solution_js = json.loads(json.dumps(solution_obj.__dict__))
            js['solutions'].append(solution_js)
        return json.dumps(js)

class Connections:

    logger = drm_logger.configure_logging("parser_sqlite_json.Connections")

    @drm_logger.log_decorator(logger) 
    def get_connection_by_solution_id_and_name(db_file_name, release_id, solution_id, name, connection_obj):
        """ 
        Return solution connection details by solution_id and name
        :param db_file_name: Database file name
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param name: Connection name
        :param connection_obj: Connection object
        :return: Connection details (JSON)
        """
        js = json.loads('{"connections":[]}')
        drm_db = Db(db_file_name)
        #=====================================================
        # Get Connection info by Solution ID & Connection name
        #=====================================================
        sql_command = "select id, name, solution_id, connection_type_id, connection_string, is_active from connections where solution_id = {sol_id} and name = '{name}';".format(sol_id = solution_id, name = name)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            connection_obj.id = row[0]    
            connection_obj.name = row[1]    
            connection_obj.solution_id = row[2]    
            connection_obj.connection_type_id = row[3]    
            connection_obj.connection_string = row[4]    
            connection_obj.is_active = row[5] 
            connection_js = json.loads(json.dumps(connection_obj.__dict__))
            js['connections'].append(connection_js)
        return json.dumps(js)
    
    @drm_logger.log_decorator(logger) 
    def get_connections(db_file_name):
        """ 
        Get a Connections
        :param db_file_name: Database file name
        :return: Connections
        """
        drm_db = Db(db_file_name)
        #=====================================================
        # Get Connection info by Solution ID & Connection name
        #=====================================================
        sql_command = "select id,connection_string from connections;"
        rows = drm_db.select_query(sql_command)
        return rows
    
class SqlScriptsVariables:

    logger = drm_logger.configure_logging("parser_sqlite_json.SqlScriptsVariables")

    @drm_logger.log_decorator(logger) 
    def get_sql_scripts_variables_by_solution_id(db_file_name, release_id, solution_id, sql_script_variable_obj):
        """ 
        Return solution sql_scripts_variables details by solution_id
        :param db_file_name: Database file name
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param sql_script_variable_obj: Sql_Scripts_Variable object
        :return: SQL Scripts variables & values (JSON)
        """
        js = json.loads('{"sql_scripts_variables":[]}')
        drm_db = Db(db_file_name)
        #==============================================
        # Get SQL Scripts variables info by Solution ID
        #==============================================
        sql_command = "select id, name, solution_id, value from sql_scripts_variables where solution_id = {sol_id} order by id;".format(sol_id = solution_id)
        rows = drm_db.select_query(sql_command)
        for row in rows:
            sql_script_variable_obj.id = row[0]    
            sql_script_variable_obj.name = row[1]    
            sql_script_variable_obj.solution_id = row[2]    
            sql_script_variable_obj.value = row[3]    
            sql_script_variable_js = json.loads(json.dumps(sql_script_variable_obj.__dict__))
            js['sql_scripts_variables'].append(sql_script_variable_js)
        return json.dumps(js)

class SqlScripts:

    logger = drm_logger.configure_logging("parser_sqlite_json.SqlScripts")

    @drm_logger.log_decorator(logger) 
    def get_sql_scripts_by_solution_id(db_file_name, release_id, solution_id, sql_script_obj):
        """ 
        Return solution sql_scripts details by solution_id
        :param db_file_name: Database file name
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param sql_script_obj: Sql_Script object
        :return: Get databases from queriy scripts (JSON)
        """
        js = json.loads('{"sql_scripts":[]}')
        drm_db = Db(db_file_name)
        #====================================
        # Get SQL Scripts info by Solution ID
        #====================================
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

    logger = drm_logger.configure_logging("parser_sqlite_json.Projects")

    @drm_logger.log_decorator(logger) 
    def get_projects_by_solution_id(db_file_name, release_id, solution_id, project_obj):
        """ 
        Return solution projects details by solution_id
        :param db_file_name: Database file name
        :param release_id: Release ID
        :param solution_id: Solution ID
        :param project_obj: Project object
        :return: Projects info (JSON)
        """
        js = json.loads('{"projects":[]}')
        drm_db = Db(db_file_name)
        #=================================
        # Get Projects info by Solution ID
        #=================================
        sql_command = "select projects.id, projects.name, projects.solution_id, projects.ordinal, targets_compare_db, targets_type_id, targets_list, targets_sql_script_id, sql_scripts.sql_text as targets_sql_text, max_degree_in_parallel, timeout_in_min, sleep_time_in_sec, deployment_properties, fail_on_error, is_active from projects left join sql_scripts on projects.solution_id = sql_scripts.solution_id and projects.targets_sql_script_id = sql_scripts.id where projects.solution_id = {sol_id} order by projects.ordinal, projects.id;".format(sol_id = solution_id)
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
            project_obj.deployment_properties = row[12] 
            project_obj.fail_on_error = row[13]    
            project_obj.is_active = row[14]    
            project_js = json.loads(json.dumps(project_obj.__dict__))
            js['projects'].append(project_js)
        return json.dumps(js)


class Deployments:

    logger = drm_logger.configure_logging("parser_sqlite_json.Deployments")

    DEPLOYMENT_PENDING_STATUS = "Pending"
    DEPLOYMENT_IN_PROGRESS_STATUS = "In progress"
    DEPLOYMENT_SUCCESS_STATUS = "Finished successfully"
    DEPLOYMENT_CANCELED_STATUS = "Canceled"
    DEPLOYMENT_FAILED_STATUS = "Failed"
    DEPLOYMENT_ALREADY_DEPLOYED_STATUS = "Already deployed"
    DRYRUN_MODE = "DryRun"
    DEPLOY_MODE = "Deploy"

    @drm_logger.log_decorator(logger) 
    def __init__(self, release_id, connection, execution_mode, deploy_dir = None, db_file_name = None): 
        """ 
        :param release_id: Release ID
        :param connection: Connection name
        :param execution_mode: Execution mode
        :param deploy_dir: Directory of all deployments files
        :param db_file_name: DRM database file name (Not in use)
        :return:
        """
        self.release_id = release_id
        self.connection = connection
        self.drm_db = Db(db_file_name)
        
        if(execution_mode == Deployments.DEPLOY_MODE):
            self.deployment_type_id = 2
        else:
            self.deployment_type_id = 1                     

    @drm_logger.log_decorator(logger) 
    def get_last_deployment_restuls(self, solution_id, project_id, targets_list_js): 
        """ 
        Return last deployment results for each target database
        :param targets_list_js: List of target databases
        :return: Last failed deployment ID (Integer) & List of target databases followed by deployment status (JSON)
        """
        task_statuses = {}
        last_deployment_id = None
         
        #=============================
        # Check last deployment status
        #=============================
        sql_command = f"select d.id, d.deployment_status_id from deployments as d inner join connections as c on c.id = d.connection_id where release_id = {self.release_id} and c.name = '{self.connection}' and d.deployment_type_id = {self.deployment_type_id} order by d.start_time desc limit 1"
        rows = self.drm_db.select_query(sql_command)
        for row in rows:
            last_deployment_id = row[0]
            deployment_status_id = row[1]
        
        #========================================================================================
        # If last deployment did not fully succeeded --> get last status for each target database
        #========================================================================================
        if (deployment_status_id != 2):
            
            sql_command = f"with deployment_try_cte as (select max(id) as id from deployments_tries as dt where deployment_id = '{last_deployment_id}') select dp.target_database_name, dp.deployment_status_id, dst.name, dp.start_time, dp.end_time from deployment_try_cte as dt inner join deployments_solutions as ds on ds.deployment_try_id = dt.id inner join deployments_projects as dp on dp.deployment_solution_id = ds.id inner join deployment_statuses as dst on dst.id = dp.deployment_status_id where ds.solution_id = {solution_id} and dp.project_id = {project_id} order by dp.start_time"
            rows2 = self.drm_db.select_query(sql_command)
            for row2 in rows2:         
                task_statuses[row2[0]] = {"status_id": row2[1], "status_name": row2[2], "start_time": row2[3], "end_time": row2[4], "error_message": None}
        
            # mark all other rest pending target databases
            for target_db in targets_list_js:
                if target_db not in task_statuses:
                    task_statuses[target_db] = {"status_id": 0, "status_name": Deployments.DEPLOYMENT_PENDING_STATUS, "start_time": None, "end_time": None, "error_message": None}
                        
        return last_deployment_id, task_statuses
        
class ChangePassword:
    
    logger = drm_logger.configure_logging("parser_sqlite_json.ChangePassword")

    @drm_logger.log_decorator(logger) 
    def __init__(self, db_file_name = "",encryption_key = "",new_encryption_key = ""):   
        """ 
        Constructor
        :param db_file_name:  databae name
        :param encryption_key: encryption_key
        :param new_encryption_key: new_encryption_key
        :return:
        """
        self.db_file_name = db_file_name
        self.encryption_key = encryption_key
        self.new_encryption_key = new_encryption_key

    @drm_logger.log_decorator(logger)     
    def execute_command(self):
        """ 
        Run ChangePassword command 
        :return: result
        """
        db_file_name = self.db_file_name
        rows = Connections.get_connections(db_file_name)
        from modules import crypto
        crpt = crypto.Crypto(self.encryption_key)
        crpt_new = crypto.Crypto(self.new_encryption_key)
        new_rows = list()

        for r in rows:
            #verify encyption key
            if (self.encryption_key != None and self.new_encryption_key != None):
                value = crpt_new.encrypt_string( crpt.decrypt_string(r[1]))
            elif (self.encryption_key == None and self.new_encryption_key != None):
                value = crpt_new.encrypt_string( r[1])
            elif (self.new_encryption_key == None and self.encryption_key != None):
                value = crpt.decrypt_string(r[1])
            else:
                raise Exception('Failed ChangePassword, No Encyption keys supplied')
            tuple_element = ((r[0],value))
            new_rows.append(tuple_element)
        new_rows = tuple(new_rows)
        self.reencrypt(db_file_name,new_rows)

    @drm_logger.log_decorator(logger) 
    def reencrypt(self,db_file_name, rows):
        """ 
        ReEncrypt
        :param db_file_name: Database file name
        :param rows: rows [id][connection_string]
        :return: Result
        """
        drm_db = Db(db_file_name)

        for row in rows:
            update_command = f"set connection_string = '{row[1]}'"
            sql_command = f"update connections {update_command} where id = {row[0] }"
            drm_db.execute_command(sql_command)
        return True