
import { getRelation } from "../api";

export interface RelationView {
  columns: Array<string>
  rows: Array<{ [key: string]: any }> // ? represents the string-key, arbitrary-value type, for example [{"id": 2, "name": "mehdi"}, {"id": 1, "name": "fuad"}]}
}

const RelationView = await getRelation('sharenstay')

const TableView = () => {
    return (
        <div id="sub-view">
            <p>The view of your relation:</p>
            {
                RelationView.columns.length > 0 &&
                <table>
                    <tr>
                        {
                            RelationView.columns.map(col => {
                                return <th>{col}</th>
                            })
                        }
                    </tr>
                    {
                        RelationView .rows.map(row => {
                            return <tr>
                                {
                                    RelationView.columns.map(col => {
                                        return <td>{row[col]}</td>
                                    })
                                }
                            </tr>
                        })
                    }


                </table>
            }
        </div>
    )
}

export default TableView