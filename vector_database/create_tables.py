import sys
import os
import pandas as pd
import lancedb
from .utils.file_processing import get_name_and_input_dir, get_special_files, process_special_files
from .utils.text_processing import clip_text_to_max_tokens, create_markdown_dataframe
from .models import Method, Class
from .config import MAX_TOKENS

def main():
    if len(sys.argv) != 2:
        print("Usage: python -m vector_database.main <code_base_path>")
        sys.exit(1)

    codebase_path = sys.argv[1]
    table_name, input_directory = get_name_and_input_dir(codebase_path)
    method_data_file = os.path.join(input_directory, "method_data.csv")
    class_data_file = os.path.join(input_directory, "class_data.csv")

    special_files = get_special_files(codebase_path)
    special_contents = process_special_files(special_files)

    method_data = pd.read_csv(method_data_file)
    class_data = pd.read_csv(class_data_file)

    print(class_data.head())

    uri = "database"
    db = lancedb.connect(uri)

    try:
        # Create and populate method table
        table = db.create_table(
            table_name + "_method", 
            schema=Method, 
            mode="overwrite",
            on_bad_vectors='drop'
        )

        method_data['code'] = method_data['source_code']
        method_data = method_data.fillna('empty')
        print("Adding method data to table")
        table.add(method_data)
    
        # Create and populate class table
        class_table = db.create_table(
            table_name + "_class", 
            schema=Class, 
            mode="overwrite",
            on_bad_vectors='drop'
        )
        class_data = class_data.fillna('')

        class_data['source_code'] = class_data.apply(
            lambda row: "File: " + row['file_path'] + "\n\n" +
                      "Class: " + row['class_name'] + "\n\n" +
                      "Source Code:\n" + 
                      clip_text_to_max_tokens(row['source_code'], MAX_TOKENS) + "\n\n",
            axis=1
        )

        if len(class_data) == 0:
            columns = ['source_code', 'file_path', 'class_name', 'constructor_declaration', 
                      'method_declarations', 'references']
            empty_data = {col: ["empty"] for col in columns}
            class_data = pd.DataFrame(empty_data)
            
        print("Adding class data to table")
        class_table.add(class_data)

        if len(special_contents) > 0:
            markdown_df = create_markdown_dataframe(special_contents)
            print(f"Adding {len(markdown_df)} special files to table")
            class_table.add(markdown_df)

        print("Embedded method data successfully")
        print("Embedded class data successfully")

    except Exception as e:
        if codebase_path in db:
            db.drop_table(codebase_path)
        raise e

if __name__ == "__main__":
    main() 